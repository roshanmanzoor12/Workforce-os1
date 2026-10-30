"use client";

import { useEffect, useRef, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
import { api } from "@/lib/api/client";

type Signal = {
  type: "offer" | "answer";
  sdp: string;
};

type Room = {
  id: string;
  employee_id: string;
  status: "pending" | "offered" | "connected" | "ended";
  offer: Signal | null;
  answer: Signal | null;
};

const ICE: RTCConfiguration = {
  iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
};

async function waitIce(pc: RTCPeerConnection): Promise<void> {
  if (pc.iceGatheringState === "complete") {
    return;
  }

  await new Promise<void>((resolve) => {
    const timeout = window.setTimeout(() => {
      pc.removeEventListener("icegatheringstatechange", changed);
      resolve();
    }, 12000);

    function changed() {
      if (pc.iceGatheringState === "complete") {
        window.clearTimeout(timeout);
        pc.removeEventListener("icegatheringstatechange", changed);
        resolve();
      }
    }

    pc.addEventListener("icegatheringstatechange", changed);
  });
}

export default function BrowserScreenSharePanel({
  selectedEmployeeId,
  requestSignal = 0,
  incomingOnly = false,
}: {
  selectedEmployeeId?: string;
  requestSignal?: number;
  incomingOnly?: boolean;
}) {
  const { workspaceId, membership } = useWorkspace();

  const owner = ["owner", "admin"].includes(
    (membership?.role_key || "").toLowerCase()
  );

  const [, setMessage] = useState("Not sharing");

  const [, setEmployees] = useState<
    { id: string; full_name: string; user_id: string | null }[]
  >([]);

  const [employeeId, setEmployeeId] = useState("");
  const [room, setRoom] = useState<Room | null>(null);
  const [pending, setPending] = useState<Room[]>([]);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const roomRef = useRef<Room | null>(null);
  const busyRef = useRef(false);
  const handledRequestSignal = useRef(0);

  const base = workspaceId
    ? `/workspaces/${workspaceId}/browser-screen-share`
    : "";

  const setCurrent = (value: Room | null) => {
    roomRef.current = value;
    setRoom(value);
  };

  const release = () => {
    pcRef.current?.close();
    pcRef.current = null;

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const stop = async () => {
    const current = roomRef.current;

    release();
    setCurrent(null);
    setMessage("Sharing ended");

    if (current && base) {
      try {
        await api.post(`${base}/requests/${current.id}/stop`, {});
      } catch {
        // Connection may already be closed.
      }
    }
  };

  useEffect(() => {
    return () => {
      release();
    };
  }, []);

  useEffect(() => {
    if (!base || !owner) {
      return;
    }

    void api
      .get<{
        employees: {
          id: string;
          full_name: string;
          user_id: string | null;
        }[];
      }>(`/workspaces/${workspaceId}/employees`)
      .then((response) => {
        const linkedEmployees = response.employees.filter(
          (employee) => employee.user_id
        );

        setEmployees(linkedEmployees);
        setEmployeeId((current) => current || linkedEmployees[0]?.id || "");
      })
      .catch((error) => {
        setMessage(String(error));
      });
  }, [base, owner, workspaceId]);

  useEffect(() => {
    if (!base) {
      return;
    }

    let active = true;

    async function poll() {
      if (busyRef.current) {
        return;
      }

      try {
        if (!owner) {
          const response = await api.get<{ requests: Room[] }>(
            `${base}/inbox`
          );

          if (active) {
            setPending(
              response.requests.filter(
                (request) => request.status === "pending"
              )
            );
          }
        }

        const current = roomRef.current;

        if (!current) {
          return;
        }

        const latest = await api.get<Room>(
          `${base}/requests/${current.id}`
        );

        if (!active) {
          return;
        }

        if (latest.status === "ended") {
          release();
          setCurrent(null);
          setMessage("Remote participant ended sharing");
          return;
        }

        if (
          owner &&
          latest.status === "offered" &&
          latest.offer &&
          !pcRef.current
        ) {
          busyRef.current = true;

          try {
            const pc = new RTCPeerConnection(ICE);
            pcRef.current = pc;

            pc.ontrack = (event) => {
              if (videoRef.current) {
                videoRef.current.srcObject =
                  event.streams[0] ?? null;
              }
            };

            await pc.setRemoteDescription(latest.offer);
            await pc.setLocalDescription(await pc.createAnswer());
            await waitIce(pc);

            const localDescription = pc.localDescription;

            if (localDescription?.sdp) {
              await api.post(
                `${base}/requests/${latest.id}/signal`,
                {
                  type: "answer",
                  sdp: localDescription.sdp,
                }
              );
            }

            setMessage("Connecting to employee screen...");
          } finally {
            busyRef.current = false;
          }
        }

        if (
          !owner &&
          latest.status === "connected" &&
          latest.answer &&
          pcRef.current &&
          !pcRef.current.remoteDescription
        ) {
          await pcRef.current.setRemoteDescription(latest.answer);
          setMessage("Screen sharing connected");
        }
      } catch (error) {
        if (active) {
          setMessage(
            error instanceof Error
              ? error.message
              : "Connection error"
          );
        }
      }
    }

    void poll();

    const interval = window.setInterval(() => {
      void poll();
    }, 1500);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [base, owner]);

  async function request() {
    if (!employeeId || !base) {
      return;
    }

    try {
      const response = await api.post<Room>(
        `${base}/requests`,
        {
          employee_id: employeeId,
        }
      );

      setCurrent(response);
      setMessage("Waiting for employee approval...");
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Request failed"
      );
    }
  }

  useEffect(() => {
    if (
      !owner ||
      !base ||
      !selectedEmployeeId ||
      requestSignal === 0 ||
      handledRequestSignal.current === requestSignal
    ) {
      return;
    }

    handledRequestSignal.current = requestSignal;

    if (roomRef.current) {
      setMessage(
        "End the current sharing session before requesting another."
      );
      return;
    }

    void api
      .post<Room>(`${base}/requests`, {
        employee_id: selectedEmployeeId,
      })
      .then((response) => {
        setCurrent(response);
        setEmployeeId(selectedEmployeeId);
        setMessage("Request sent to employee.");
      })
      .catch((error: unknown) => {
        setMessage(
          error instanceof Error ? error.message : "Request failed"
        );
      });
  }, [
    base,
    owner,
    requestSignal,
    selectedEmployeeId,
  ]);

  async function accept(invite: Room) {
    if (!base || busyRef.current) {
      return;
    }

    busyRef.current = true;

    try {
      const stream =
        await navigator.mediaDevices.getDisplayMedia({
          video: {
            frameRate: 12,
          },
          audio: false,
        });

      streamRef.current = stream;

      const pc = new RTCPeerConnection(ICE);
      pcRef.current = pc;

      for (const track of stream.getTracks()) {
        pc.addTrack(track, stream);
      }

      stream
        .getVideoTracks()[0]
        ?.addEventListener(
          "ended",
          () => void stop(),
          { once: true }
        );

      await pc.setLocalDescription(await pc.createOffer());
      await waitIce(pc);

      const localDescription = pc.localDescription;

      if (!localDescription?.sdp) {
        throw new Error("Unable to generate WebRTC offer");
      }

      await api.post(
        `${base}/requests/${invite.id}/signal`,
        {
          type: "offer",
          sdp: localDescription.sdp,
        }
      );

      setCurrent({
        ...invite,
        status: "offered",
      });

      setPending([]);
      setMessage("Sharing permission granted.");
    } catch (error) {
      release();

      setMessage(
        error instanceof Error
          ? error.message
          : "Screen selection cancelled"
      );
    } finally {
      busyRef.current = false;
    }
  }

  return (
    <>
      {!owner && pending.length > 0 && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Incoming screen-sharing request"
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            background: "rgba(11,17,27,.75)",
            display: "grid",
            placeItems: "center",
            padding: 20,
          }}
        >
          <div
            style={{
              background: "white",
              color: "#152137",
              borderRadius: 14,
              padding: 24,
              maxWidth: 480,
              width: "100%",
              boxShadow: "0 20px 70px #0005",
            }}
          >
            <h2
              style={{
                fontSize: 22,
                fontWeight: 750,
                marginBottom: 12,
              }}
            >
              Incoming screen-sharing request
            </h2>

            <p
              style={{
                lineHeight: 1.6,
                marginBottom: 18,
              }}
            >
              Your workspace owner has requested to view your
              screen. Nothing is captured until you explicitly
              select a screen or window.
            </p>

            {pending.map((invite) => (
              <div
                key={invite.id}
                style={{
                  display: "flex",
                  gap: 10,
                  flexWrap: "wrap",
                  marginTop: 12,
                }}
              >
                <button
                  type="button"
                  onClick={() => void accept(invite)}
                  style={{
                    padding: "11px 16px",
                    background: "#166534",
                    color: "white",
                    borderRadius: 8,
                  }}
                >
                  Accept &amp; choose screen
                </button>

                <button
                  type="button"
                  onClick={() =>
                    void api
                      .post(
                        `${base}/requests/${invite.id}/stop`,
                        {}
                      )
                      .then(() =>
                        setPending((old) =>
                          old.filter(
                            (request) =>
                              request.id !== invite.id
                          )
                        )
                      )
                  }
                  style={{
                    padding: "11px 16px",
                    border: "1px solid #bbc5d2",
                    borderRadius: 8,
                  }}
                >
                  Decline
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {!incomingOnly && (
        <section
          style={{
            width: "100%",
            minHeight: 380,
            display: "flex",
            flexDirection: "column",
            background: "#111",
            color: "white",
            padding: 16,
            gap: 12,
          }}
          aria-label="Employee-approved live screen viewer"
        >
          <video
            ref={videoRef}
            playsInline
            autoPlay
            controls={false}
            style={{
              width: "100%",
              flex: 1,
              minHeight: 320,
              objectFit: "contain",
              background: "#111",
              borderRadius: 6,
            }}
          />
        </section>
      )}
    </>
  );
}