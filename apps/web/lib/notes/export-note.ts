export function normalizeNoteLink(value: string) {
  let input = value.trim();

  if (!input || /\s/.test(input)) {
    throw new Error("Enter a valid link.");
  }

  if (!/^[a-z][a-z0-9+.-]*:/i.test(input)) {
    input = `https://${input}`;
  }

  const url = new URL(input);

  if (
    !["https:", "http:", "mailto:", "tel:"].includes(
      url.protocol,
    )
  ) {
    throw new Error(
      "Use an HTTP, HTTPS, email or telephone link.",
    );
  }

  if (url.username || url.password) {
    throw new Error(
      "Links with embedded credentials are not supported.",
    );
  }

  return url.href;
}

type FileHandle = {
  createWritable: () => Promise<{
    write: (data: string) => Promise<void>;
    close: () => Promise<void>;
    abort: () => Promise<void>;
  }>;
};

type PickerWindow = Window & {
  showSaveFilePicker?: (options: {
    suggestedName: string;
    types: Array<{
      description: string;
      accept: Record<string, string[]>;
    }>;
  }) => Promise<FileHandle>;
};

export async function exportNoteText(
  title: string,
  html: string,
  tags: string[],
) {
  const container = document.createElement("div");
  container.innerHTML = html;

  container
    .querySelectorAll("script,style,iframe,object")
    .forEach((element) => element.remove());

  container.querySelectorAll("a").forEach((link) => {
    const href = link.getAttribute("href") ?? "";
    const text = link.textContent ?? href;

    link.replaceWith(
      document.createTextNode(
        text === href
          ? text
          : `${text} (${href})`,
      ),
    );
  });

  container.querySelectorAll("li").forEach((item) => {
    const list = item.parentElement;

    const prefix = list?.hasAttribute("data-checklist")
      ? item.getAttribute("data-checked") === "true"
        ? "[x] "
        : "[ ] "
      : list?.tagName === "OL"
        ? `${Array.from(list.children).indexOf(item) + 1}. `
        : "- ";

    item.prepend(document.createTextNode(prefix));
  });

  container.querySelectorAll("br").forEach((br) => {
    br.replaceWith("\n");
  });

  container
    .querySelectorAll(
      "p,div,h1,h2,h3,h4,li,blockquote,pre",
    )
    .forEach((element) => {
      element.append(document.createTextNode("\n"));
    });

  container.querySelectorAll("img").forEach((image) => {
    image.replaceWith(
      document.createTextNode(
        `[Image: ${image.alt || "Image"}]`,
      ),
    );
  });

  const body = (container.textContent ?? "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  const text = [
    title.trim() || "Untitled Note",
    "",
    body,
    ...(tags.length
      ? ["", `Tags: ${tags.join(", ")}`]
      : []),
    "",
  ].join("\n");

  let name = (title.trim() || "Untitled Note")
    .replace(/[<>:"/\\|?*\x00-\x1f]/g, "_")
    .replace(/[. ]+$/g, "")
    .slice(0, 120);

  if (
    !name ||
    /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(name)
  ) {
    name = `Note-${name || "export"}`;
  }

  const filename = `${name.replace(/\.txt$/i, "")}.txt`;
  const picker = window as PickerWindow;

  if (picker.showSaveFilePicker) {
    const handle = await picker.showSaveFilePicker({
      suggestedName: filename,
      types: [
        {
          description: "Text document",
          accept: {
            "text/plain": [".txt"],
          },
        },
      ],
    });

    const writable = await handle.createWritable();

    try {
      await writable.write(text);
      await writable.close();
    } catch (error) {
      try {
        await writable.abort();
      } catch {
        // Preserve the original write error.
      }

      throw error;
    }

    return;
  }

  const url = URL.createObjectURL(
    new Blob([text], {
      type: "text/plain;charset=utf-8",
    }),
  );

  const link = document.createElement("a");
  link.href = url;
  link.download = filename;

  document.body.append(link);
  link.click();
  link.remove();

  window.setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 60000);
}