const EMOJI_UNIT =
  "(?:" +
  "\\p{Regional_Indicator}{2}" +
  "|" +
  "[#*0-9]\\uFE0F?\\u20E3" +
  "|" +
  "\\p{Extended_Pictographic}" +
  "[\\uFE0E\\uFE0F]?" +
  "\\p{Emoji_Modifier}?" +
  "(?:[\\u{E0020}-\\u{E007E}]+\\u{E007F})?" +
  ")";

const SINGLE_EMOJI = new RegExp(
  `^${EMOJI_UNIT}(?:\\u200D${EMOJI_UNIT})*$`,
  "u",
);

export function isSingleEmojiMessage(
  content: string | null | undefined,
): boolean {
  return SINGLE_EMOJI.test(content?.trim() ?? "");
}