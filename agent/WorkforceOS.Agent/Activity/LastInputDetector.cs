using System.ComponentModel;
using System.Runtime.InteropServices;

namespace WorkforceOS.Agent.Activity;

public sealed class LastInputDetector
{
    public LastInputSnapshot GetSnapshot()
    {
        LASTINPUTINFO lastInputInfo =
            new()
            {
                cbSize =
                    (uint)Marshal.SizeOf<
                        LASTINPUTINFO
                    >()
            };

        bool success =
            GetLastInputInfo(
                ref lastInputInfo
            );

        if (!success)
        {
            throw new Win32Exception(
                Marshal.GetLastWin32Error(),
                "Unable to read Windows last-input information."
            );
        }

        uint currentTickCount =
            GetTickCount();

        /*
         * LASTINPUTINFO.dwTime and GetTickCount() are both
         * 32-bit millisecond counters.
         *
         * The subtraction intentionally uses unchecked uint
         * arithmetic so the Windows tick counter wrap at roughly
         * 49.7 days is handled correctly.
         */
        uint idleMilliseconds =
            unchecked(
                currentTickCount
                - lastInputInfo.dwTime
            );

        long idleSeconds =
            idleMilliseconds
            / 1000L;

        DateTimeOffset observedAt =
            DateTimeOffset.UtcNow;

        DateTimeOffset lastInputAt =
            observedAt.Subtract(
                TimeSpan.FromMilliseconds(
                    idleMilliseconds
                )
            );

        return new LastInputSnapshot
        {
            ObservedAt =
                observedAt,

            LastInputAt =
                lastInputAt,

            IdleSeconds =
                idleSeconds
        };
    }

    [DllImport(
        "user32.dll",
        SetLastError = true
    )]
    [return: MarshalAs(
        UnmanagedType.Bool
    )]
    private static extern bool GetLastInputInfo(
        ref LASTINPUTINFO plii
    );

    [DllImport(
        "kernel32.dll"
    )]
    private static extern uint GetTickCount();

    [StructLayout(
        LayoutKind.Sequential
    )]
    private struct LASTINPUTINFO
    {
        public uint cbSize;

        public uint dwTime;
    }
}


public sealed record LastInputSnapshot
{
    public required DateTimeOffset ObservedAt
    {
        get;
        init;
    }

    public required DateTimeOffset LastInputAt
    {
        get;
        init;
    }

    public required long IdleSeconds
    {
        get;
        init;
    }
}