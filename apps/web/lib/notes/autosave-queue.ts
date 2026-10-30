export interface QueueSnapshot {
  saving: boolean;
  error: string | null;
}

export function createAutosaveQueue<T, R>(options: {
  initial: T;
  initialSignature: string;
  acknowledged: boolean;
  persist: (value: T) => Promise<R>;
  onSaved?: (result: R, value: T) => void;
  onState?: (state: QueueSnapshot) => void;
}) {
  let latest = {
    value: options.initial,
    signature: options.initialSignature,
  };

  let acknowledged: string | null = options.acknowledged
    ? latest.signature
    : null;

  let pending: Promise<void> | null = null;
  let error: string | null = null;

  const snapshot = (): QueueSnapshot => ({
    saving: pending !== null,
    error,
  });

  const notify = () => {
    options.onState?.(snapshot());
  };

  function start() {
    error = null;

    const task = Promise.resolve().then(async () => {
      try {
        while (acknowledged !== latest.signature) {
          const request = latest;

          const result = await options.persist(request.value);

          acknowledged = request.signature;
          options.onSaved?.(result, request.value);
        }
      } catch (cause) {
        // The request may have reached the server even if its
        // response was lost. Retry the latest complete snapshot.
        acknowledged = null;

        error =
          cause instanceof Error
            ? cause.message
            : "Unable to save this note.";

        throw cause;
      }
    });

    pending = task.finally(() => {
      pending = null;
      notify();
    });

    notify();

    return pending;
  }

  return {
    update(
      value: T,
      signature: string,
      matchesServer = false,
    ) {
      latest = { value, signature };

      if (
        matchesServer &&
        pending === null &&
        error === null
      ) {
        acknowledged = signature;
      }
    },

    async flush() {
      while (
        pending !== null ||
        acknowledged !== latest.signature
      ) {
        await (pending ?? start());
      }
    },

    snapshot,
  };
}