"use client";
import { useEffect, useRef, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";

type Signal = { type: "offer" | "answer"; sdp: string };
type Room = { id: string; employee_id: string; status: "pending" | "offered" | "connected" | "ended"; offer: Signal | null; answer: Signal | null };
const ICE: RTCConfiguration = { iceServers: [{ urls: "stun:stun.l.google.com:19302" }] };

async function waitIce(pc: RTCPeerConnection): Promise<void> {
  if (pc.iceGatheringState === "complete") return;
  await new Promise<void>((resolve) => {
    const timeout = window.setTimeout(() => { pc.removeEventListener("icegatheringstatechange", changed); resolve(); }, 12000);
    function changed() { if (pc.iceGatheringState === "complete") { window.clearTimeout(timeout); pc.removeEventListener("icegatheringstatechange", changed); resolve(); } }
    pc.addEventListener("icegatheringstatechange", changed);
  });
}

export default function BrowserScreenSharePanel() {
  const { workspaceId, membership } = useWorkspace();
  const owner = ["owner", "admin"].includes((membership?.role_key || "").toLowerCase());
  const [employees, setEmployees] = useState<{id:string;full_name:string;user_id:string|null}[]>([]);
  const [employeeId, setEmployeeId] = useState("");
  const [room, setRoom] = useState<Room | null>(null);
  const [pending, setPending] = useState<Room[]>([]);
  const [message, setMessage] = useState("Not sharing");
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const roomRef = useRef<Room | null>(null);
  const busyRef = useRef(false);
  const base = workspaceId ? `/workspaces/${workspaceId}/browser-screen-share` : "";
  const setCurrent = (value: Room | null) => { roomRef.current = value; setRoom(value); };

  const release = () => {
    pcRef.current?.close(); pcRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop()); streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  };
  const stop = async () => {
    const current = roomRef.current;
    release(); setCurrent(null); setMessage("Sharing ended");
    if (current && base) { try { await api.post(`${base}/requests/${current.id}/stop`, {}); } catch { /* connection lost */ } }
  };
  useEffect(() => () => { release(); }, []);
  useEffect(() => {
    if (!base || !owner) return;
    void api.get<{employees: typeof employees}>(`/workspaces/${workspaceId}/employees`).then(r => {
      const linked = r.employees.filter(e => e.user_id);
      setEmployees(linked); setEmployeeId(v => v || linked[0]?.id || "");
    }).catch(e => setMessage(String(e)));
  }, [base, owner, workspaceId]);

  useEffect(() => {
    if (!base) return;
    let active = true;
    async function poll() {
      if (busyRef.current) return;
      try {
        if (!owner) {
          const r = await api.get<{requests:Room[]}>(`${base}/inbox`);
          if (active) setPending(r.requests.filter(i => i.status === "pending"));
        }
        const current = roomRef.current;
        if (!current) return;
        const latest = await api.get<Room>(`${base}/requests/${current.id}`);
        if (!active) return;
        if (latest.status === "ended") { release(); setCurrent(null); setMessage("Remote participant ended sharing"); return; }
        if (owner && latest.status === "offered" && latest.offer && !pcRef.current) {
          busyRef.current = true;
          try {
            const pc = new RTCPeerConnection(ICE); pcRef.current = pc;
            pc.ontrack = (event) => { if (videoRef.current) videoRef.current.srcObject = event.streams[0] ?? null; };
            await pc.setRemoteDescription(latest.offer);
            await pc.setLocalDescription(await pc.createAnswer()); await waitIce(pc);
            const local = pc.localDescription;
            if (local?.sdp) await api.post(`${base}/requests/${latest.id}/signal`, {type:"answer",sdp:local.sdp});
            setMessage("Connecting to employee screen...");
          } finally { busyRef.current = false; }
        }
        if (!owner && latest.status === "connected" && latest.answer && pcRef.current && !pcRef.current.remoteDescription) {
          await pcRef.current.setRemoteDescription(latest.answer);
          setMessage("Screen sharing active — click Stop Sharing to end");
        }
      } catch (err) { if (active) setMessage(err instanceof Error ? err.message : "Connection error"); }
    }
    void poll(); const interval = window.setInterval(() => void poll(), 1500);
    return () => { active = false; window.clearInterval(interval); };
  }, [base, owner]);

  async function request() {
    if (!employeeId || !base) return;
    try { const r = await api.post<Room>(`${base}/requests`, { employee_id: employeeId }); setCurrent(r); setMessage("Waiting for employee to accept..."); }
    catch (err) { setMessage(err instanceof Error ? err.message : "Request failed"); }
  }
  async function accept(invite: Room) {
    if (!base || busyRef.current) return;
    busyRef.current = true;
    try {
      // Browser's native chooser requires explicit click; nothing is captured silently.
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: { frameRate: 12 }, audio: false });
      streamRef.current = stream;
      const pc = new RTCPeerConnection(ICE); pcRef.current = pc;
      for (const track of stream.getTracks()) pc.addTrack(track, stream);
      stream.getVideoTracks()[0]?.addEventListener("ended", () => void stop(), {once:true});
      await pc.setLocalDescription(await pc.createOffer()); await waitIce(pc);
      const local = pc.localDescription;
      if (!local?.sdp) throw new Error("Unable to generate WebRTC offer");
      await api.post(`${base}/requests/${invite.id}/signal`, {type:"offer",sdp:local.sdp});
      setCurrent({...invite, status:"offered"}); setPending([]);
      setMessage("Sharing permission granted. Waiting for viewer...");
    } catch (err) { release(); setMessage(err instanceof Error ? err.message : "Screen selection cancelled"); }
    finally { busyRef.current = false; }
  }
  return <section style={{padding:16,width:"100%",display:"grid",gap:18}}>
    <h1 style={{fontSize:28,fontWeight:700}}>Browser screen sharing</h1>
    <p>Real screen video between logged-in Chrome profiles. Sharing only starts when the employee clicks Accept and chooses a screen. This does not use Windows Agent capture.</p>
    {owner ? <section style={{display:"flex",gap:12,alignItems:"center"}}>
      <label>Employee <select value={employeeId} onChange={e=>setEmployeeId(e.target.value)} style={{padding:10,marginLeft:8}}>
        {employees.map(e=><option key={e.id} value={e.id}>{e.full_name}</option>)}
      </select></label>
      <button disabled={!employeeId || !!room} onClick={()=>void request()} style={{padding:12,background:"#232323",color:"white",borderRadius:8}}>Request Screen Share</button>
    </section> : <section>
      <h2 style={{fontWeight:700}}>Incoming screen-share requests</h2>
      {!pending.length && <p>No pending requests.</p>}
      {pending.map(r=><div key={r.id} style={{padding:12,border:"1px solid #ccc",marginTop:8}}>
        <span>Workspace owner requests screen sharing. </span>
        <button onClick={()=>void accept(r)} style={{padding:10,background:"#166534",color:"white"}}>Accept & Choose Screen</button>
        <button onClick={()=>void api.post(`${base}/requests/${r.id}/stop`,{})} style={{padding:10,marginLeft:8}}>Decline</button>
      </div>)}
    </section>}
    <div role="status" style={{padding:12,background:"#f3f4f6"}}>{message}</div>
    <video ref={videoRef} playsInline autoPlay controls={false} style={{width:"100%",background:"#17191d",aspectRatio:"16/9",borderRadius:10,objectFit:"contain"}} />
    {room && <button onClick={()=>void stop()} style={{padding:12,background:"#b91c1c",color:"white",borderRadius:8,width:190}}>Stop {owner ? "Viewing" : "Sharing"}</button>}
    <p style={{fontSize:12,color:"#64748b"}}>Development demo: one backend process, no persistent recording, no TURN server. For remote networks/production, use secure HTTPS, persistent authorized session state, and TURN.</p>
  </section>;
}
