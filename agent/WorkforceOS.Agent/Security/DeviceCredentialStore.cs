using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;

namespace WorkforceOS.Agent.Security;

public sealed class DeviceCredentialStore
{
    private const string CompanyDirectoryName =
        "WorkforceOS";

    private const string AgentDirectoryName =
        "Agent";

    private const string CredentialFileName =
        "device-credentials.dat";

    private const int CryptProtectUiForbidden =
        0x1;

    private const int CryptProtectLocalMachine =
        0x4;

    private static readonly byte[] Entropy =
        Encoding.UTF8.GetBytes(
            "WorkforceOS.Agent.DeviceCredentials.v2"
        );

    private static readonly byte[] LegacyEntropy =
        Encoding.UTF8.GetBytes(
            "WorkforceOS.Agent.DeviceCredentials.v1"
        );

    private static readonly JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web);

    // =====================================================
    // PUBLIC API
    // =====================================================

    public Task<bool> ExistsAsync(
        CancellationToken cancellationToken = default
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        return Task.FromResult(
            File.Exists(
                GetCredentialFilePath()
            )
        );
    }

    public async Task<DeviceCredentials?> LoadAsync(
        CancellationToken cancellationToken = default
    )
    {
        string path =
            GetCredentialFilePath();

        if (
            !File.Exists(
                path
            )
        )
        {
            return null;
        }

        byte[] encryptedBytes =
            await File.ReadAllBytesAsync(
                path,
                cancellationToken
            );

        if (
            encryptedBytes.Length == 0
        )
        {
            return null;
        }

        byte[]? decryptedBytes =
            null;

        bool usedLegacyEntropy =
            false;

        try
        {
            try
            {
                decryptedBytes =
                    Unprotect(
                        encryptedBytes,
                        Entropy
                    );
            }
            catch (
                Win32Exception
            )
            {
                decryptedBytes =
                    Unprotect(
                        encryptedBytes,
                        LegacyEntropy
                    );

                usedLegacyEntropy =
                    true;
            }

            DeviceCredentials? credentials =
                JsonSerializer.Deserialize<
                    DeviceCredentials
                >(
                    decryptedBytes,
                    JsonOptions
                );

            if (
                credentials is null
                || !credentials.IsValid()
            )
            {
                throw new InvalidDataException(
                    "Stored WorkforceOS device credentials are invalid."
                );
            }

            if (
                usedLegacyEntropy
                || credentials.RequiresMigration()
            )
            {
                DeviceCredentials migratedCredentials =
                    credentials with
                    {
                        FormatVersion =
                            DeviceCredentials
                                .CurrentFormatVersion,

                        StoredAt =
                            DateTimeOffset.UtcNow
                    };

                await SaveAsync(
                    migratedCredentials,
                    cancellationToken
                );

                return migratedCredentials;
            }

            return credentials;
        }
        finally
        {
            Array.Clear(
                encryptedBytes,
                0,
                encryptedBytes.Length
            );

            if (
                decryptedBytes is not null
            )
            {
                Array.Clear(
                    decryptedBytes,
                    0,
                    decryptedBytes.Length
                );
            }
        }
    }

    public async Task SaveAsync(
        DeviceCredentials credentials,
        CancellationToken cancellationToken = default
    )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        DeviceCredentials normalizedCredentials =
            credentials with
            {
                FormatVersion =
                    DeviceCredentials
                        .CurrentFormatVersion
            };

        if (
            !normalizedCredentials.IsValid()
        )
        {
            throw new ArgumentException(
                "Device credentials are invalid.",
                nameof(credentials)
            );
        }

        string directoryPath =
            GetAgentDataDirectory();

        Directory.CreateDirectory(
            directoryPath
        );

        string destinationPath =
            GetCredentialFilePath();

        string temporaryPath =
            destinationPath
            + "."
            + Guid.NewGuid().ToString(
                "N"
            )
            + ".tmp";

        byte[] plaintextBytes =
            JsonSerializer.SerializeToUtf8Bytes(
                normalizedCredentials,
                JsonOptions
            );

        byte[] protectedBytes =
            Array.Empty<byte>();

        try
        {
            protectedBytes =
                ProtectLocalMachine(
                    plaintextBytes,
                    Entropy
                );

            await File.WriteAllBytesAsync(
                temporaryPath,
                protectedBytes,
                cancellationToken
            );

            File.Move(
                temporaryPath,
                destinationPath,
                overwrite: true
            );
        }
        finally
        {
            Array.Clear(
                plaintextBytes,
                0,
                plaintextBytes.Length
            );

            if (
                protectedBytes.Length > 0
            )
            {
                Array.Clear(
                    protectedBytes,
                    0,
                    protectedBytes.Length
                );
            }

            if (
                File.Exists(
                    temporaryPath
                )
            )
            {
                try
                {
                    File.Delete(
                        temporaryPath
                    );
                }
                catch
                {
                    // Best-effort cleanup only.
                }
            }
        }
    }

    public Task DeleteAsync(
        CancellationToken cancellationToken = default
    )
    {
        cancellationToken.ThrowIfCancellationRequested();

        string path =
            GetCredentialFilePath();

        if (
            File.Exists(
                path
            )
        )
        {
            File.Delete(
                path
            );
        }

        return Task.CompletedTask;
    }

    public static string GetAgentDataDirectory()
    {
        string commonApplicationData =
            Environment.GetFolderPath(
                Environment.SpecialFolder
                    .CommonApplicationData
            );

        if (
            string.IsNullOrWhiteSpace(
                commonApplicationData
            )
        )
        {
            throw new InvalidOperationException(
                "Windows common application data directory could not be resolved."
            );
        }

        return Path.Combine(
            commonApplicationData,
            CompanyDirectoryName,
            AgentDirectoryName
        );
    }

    public static string GetCredentialFilePath()
    {
        return Path.Combine(
            GetAgentDataDirectory(),
            CredentialFileName
        );
    }

    // =====================================================
    // WINDOWS DPAPI
    // =====================================================

    private static byte[] ProtectLocalMachine(
        byte[] plaintext,
        byte[] entropy
    )
    {
        DATA_BLOB inputBlob =
            CreateDataBlob(
                plaintext
            );

        DATA_BLOB entropyBlob =
            CreateDataBlob(
                entropy
            );

        DATA_BLOB outputBlob =
            default;

        try
        {
            bool success =
                CryptProtectData(
                    ref inputBlob,
                    null,
                    ref entropyBlob,
                    IntPtr.Zero,
                    IntPtr.Zero,
                    CryptProtectUiForbidden
                    | CryptProtectLocalMachine,
                    out outputBlob
                );

            if (
                !success
            )
            {
                throw new Win32Exception(
                    Marshal.GetLastWin32Error(),
                    "Windows could not protect the WorkforceOS device credential."
                );
            }

            return CopyOutputBlob(
                outputBlob
            );
        }
        finally
        {
            FreeInputBlob(
                ref inputBlob
            );

            FreeInputBlob(
                ref entropyBlob
            );

            FreeOutputBlob(
                ref outputBlob
            );
        }
    }

    private static byte[] Unprotect(
        byte[] ciphertext,
        byte[] entropy
    )
    {
        DATA_BLOB inputBlob =
            CreateDataBlob(
                ciphertext
            );

        DATA_BLOB entropyBlob =
            CreateDataBlob(
                entropy
            );

        DATA_BLOB outputBlob =
            default;

        try
        {
            bool success =
                CryptUnprotectData(
                    ref inputBlob,
                    IntPtr.Zero,
                    ref entropyBlob,
                    IntPtr.Zero,
                    IntPtr.Zero,
                    CryptProtectUiForbidden,
                    out outputBlob
                );

            if (
                !success
            )
            {
                throw new Win32Exception(
                    Marshal.GetLastWin32Error(),
                    "Windows could not unprotect the WorkforceOS device credential."
                );
            }

            return CopyOutputBlob(
                outputBlob
            );
        }
        finally
        {
            FreeInputBlob(
                ref inputBlob
            );

            FreeInputBlob(
                ref entropyBlob
            );

            FreeOutputBlob(
                ref outputBlob
            );
        }
    }

    private static byte[] CopyOutputBlob(
        DATA_BLOB blob
    )
    {
        if (
            blob.cbData <= 0
            || blob.pbData
                == IntPtr.Zero
        )
        {
            throw new InvalidOperationException(
                "Windows DPAPI returned an empty credential payload."
            );
        }

        byte[] output =
            new byte[
                blob.cbData
            ];

        Marshal.Copy(
            blob.pbData,
            output,
            0,
            blob.cbData
        );

        return output;
    }

    private static DATA_BLOB CreateDataBlob(
        byte[] data
    )
    {
        if (
            data.Length == 0
        )
        {
            return default;
        }

        IntPtr pointer =
            Marshal.AllocHGlobal(
                data.Length
            );

        Marshal.Copy(
            data,
            0,
            pointer,
            data.Length
        );

        return new DATA_BLOB
        {
            cbData =
                data.Length,

            pbData =
                pointer
        };
    }

    private static void FreeInputBlob(
        ref DATA_BLOB blob
    )
    {
        if (
            blob.pbData
            == IntPtr.Zero
        )
        {
            return;
        }

        Marshal.FreeHGlobal(
            blob.pbData
        );

        blob.pbData =
            IntPtr.Zero;

        blob.cbData =
            0;
    }

    private static void FreeOutputBlob(
        ref DATA_BLOB blob
    )
    {
        if (
            blob.pbData
            == IntPtr.Zero
        )
        {
            return;
        }

        _ =
            LocalFree(
                blob.pbData
            );

        blob.pbData =
            IntPtr.Zero;

        blob.cbData =
            0;
    }

    // =====================================================
    // NATIVE WINDOWS DEFINITIONS
    // =====================================================

    [StructLayout(
        LayoutKind.Sequential
    )]
    private struct DATA_BLOB
    {
        public int cbData;

        public IntPtr pbData;
    }

    [DllImport(
        "Crypt32.dll",
        SetLastError = true,
        CharSet = CharSet.Unicode
    )]
    [return: MarshalAs(
        UnmanagedType.Bool
    )]
    private static extern bool CryptProtectData(
        ref DATA_BLOB pDataIn,
        string? szDataDescr,
        ref DATA_BLOB pOptionalEntropy,
        IntPtr pvReserved,
        IntPtr pPromptStruct,
        int dwFlags,
        out DATA_BLOB pDataOut
    );

    [DllImport(
        "Crypt32.dll",
        SetLastError = true,
        CharSet = CharSet.Unicode
    )]
    [return: MarshalAs(
        UnmanagedType.Bool
    )]
    private static extern bool CryptUnprotectData(
        ref DATA_BLOB pDataIn,
        IntPtr ppszDataDescr,
        ref DATA_BLOB pOptionalEntropy,
        IntPtr pvReserved,
        IntPtr pPromptStruct,
        int dwFlags,
        out DATA_BLOB pDataOut
    );

    [DllImport(
        "Kernel32.dll",
        SetLastError = true
    )]
    private static extern IntPtr LocalFree(
        IntPtr hMem
    );
}