import type {
  WorkspaceChannelMessage,
} from "@/types/channels";


export function dedupeChannelMessages(
  messages:
    WorkspaceChannelMessage[],
): WorkspaceChannelMessage[] {
  const byId =
    new Map<
      string,
      WorkspaceChannelMessage
    >();


  for (
    const message
    of messages
  ) {
    byId.set(
      message.id,
      message,
    );
  }


  return Array.from(
    byId.values(),
  ).sort(
    (
      left,
      right,
    ) => {
      const leftTime =
        new Date(
          left.created_at,
        ).getTime();

      const rightTime =
        new Date(
          right.created_at,
        ).getTime();


      if (
        leftTime
        !== rightTime
      ) {
        return (
          leftTime
          - rightTime
        );
      }


      return (
        left.id
          .localeCompare(
            right.id,
          )
      );
    },
  );
}