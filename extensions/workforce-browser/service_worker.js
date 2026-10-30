const NATIVE_HOST =
  "com.workforceos.website_tracking";

const ALARM_NAME =
  "workforceos-domain-observation";

const OBSERVATION_PERIOD_MINUTES =
  0.5;

const BADGE_CLEAR_DELAY_MS =
  5000;


function logStatus(message) {
  console.info(
    `[WorkforceOS] ${message}`
  );
}


function logError(error) {
  const message =
    error instanceof Error
      ? error.message
      : String(error);

  console.error(
    `[WorkforceOS] ${message}`
  );
}


function normalizeHostname(url) {
  try {
    const parsed =
      new URL(url);

    if (
      parsed.protocol !== "http:" &&
      parsed.protocol !== "https:"
    ) {
      return null;
    }

    let hostname =
      parsed.hostname
        .trim()
        .toLowerCase();

    if (
      hostname.startsWith("www.")
    ) {
      hostname =
        hostname.substring(4);
    }

    return hostname || null;
  } catch {
    return null;
  }
}


function detectBrowserProcess() {
  const userAgent =
    navigator.userAgent
      .toLowerCase();

  if (
    userAgent.includes("edg/")
  ) {
    return "msedge.exe";
  }

  if (
    userAgent.includes("opr/")
  ) {
    return "opera.exe";
  }

  if (
    userAgent.includes("vivaldi")
  ) {
    return "vivaldi.exe";
  }

  if (
    userAgent.includes("firefox/")
  ) {
    return "firefox.exe";
  }

  return "chrome.exe";
}


async function setBadge(text) {
  try {
    await chrome.action.setBadgeText({
      text
    });

    if (
      text === ""
    ) {
      return;
    }

    setTimeout(
      () => {
        void chrome.action.setBadgeText({
          text: ""
        });
      },
      BADGE_CLEAR_DELAY_MS
    );
  } catch {
    // Best-effort visual status only.
  }
}


async function getActiveTab() {
  const tabs =
    await chrome.tabs.query({
      active: true,
      lastFocusedWindow: true
    });

  if (
    !Array.isArray(tabs) ||
    tabs.length === 0
  ) {
    return null;
  }

  return tabs[0];
}


function sendObservation(
  observation
) {
  return new Promise(
    (resolve, reject) => {
      chrome.runtime.sendNativeMessage(
        NATIVE_HOST,
        observation,
        response => {
          const runtimeError =
            chrome.runtime.lastError;

          if (runtimeError) {
            reject(
              new Error(
                runtimeError.message
              )
            );

            return;
          }

          resolve(
            response
          );
        }
      );
    }
  );
}


async function reportActiveDomain(
  trigger
) {
  try {
    logStatus(
      `Observation triggered by ${trigger}.`
    );

    const tab =
      await getActiveTab();

    if (!tab) {
      logStatus(
        "No active browser tab available."
      );

      await setBadge(
        "?"
      );

      return;
    }

    if (
      typeof tab.url !== "string" ||
      tab.url.length === 0
    ) {
      logError(
        "Active tab URL is unavailable."
      );

      await setBadge(
        "?"
      );

      return;
    }

    const domain =
      normalizeHostname(
        tab.url
      );

    if (!domain) {
      logStatus(
        "Active tab is not an HTTP/HTTPS page."
      );

      await setBadge(
        "-"
      );

      return;
    }

    const browserProcessName =
      detectBrowserProcess();

    const observation = {
      protocolVersion: 1,

      browserProcessName,

      domain,

      pageUrl: null,

      pageTitle: null,

      observedAt:
        new Date().toISOString()
    };

    /*
     * Privacy-safe diagnostics only.
     *
     * We intentionally do NOT log:
     * - domain
     * - URL
     * - title
     * - page content
     */
    logStatus(
      `Sending observation. Browser=${browserProcessName}`
    );

    const response =
      await sendObservation(
        observation
      );

    if (
      response &&
      response.accepted === true
    ) {
      logStatus(
        "Active domain observation accepted."
      );

      await setBadge(
        "✓"
      );

      return;
    }

    if (
      response &&
      typeof response.error === "string" &&
      response.error.length > 0
    ) {
      logError(
        `Native host rejected observation: ${response.error}`
      );
    } else {
      logError(
        "Native host rejected observation without an error reason."
      );
    }

    await setBadge(
      "!"
    );
  } catch (error) {
    logError(
      error
    );

    await setBadge(
      "!"
    );
  }
}


async function ensureAlarm() {
  const existing =
    await chrome.alarms.get(
      ALARM_NAME
    );

  if (existing) {
    return;
  }

  await chrome.alarms.create(
    ALARM_NAME,
    {
      periodInMinutes:
        OBSERVATION_PERIOD_MINUTES
    }
  );

  logStatus(
    "Observation alarm created."
  );
}


chrome.runtime.onInstalled.addListener(
  details => {
    logStatus(
      `Extension installed/reloaded: ${details.reason}.`
    );

    void ensureAlarm();

    void reportActiveDomain(
      "install"
    );
  }
);


chrome.runtime.onStartup.addListener(
  () => {
    logStatus(
      "Chrome startup detected."
    );

    void ensureAlarm();

    void reportActiveDomain(
      "startup"
    );
  }
);


chrome.alarms.onAlarm.addListener(
  alarm => {
    if (
      alarm.name === ALARM_NAME
    ) {
      void reportActiveDomain(
        "alarm"
      );
    }
  }
);


chrome.tabs.onActivated.addListener(
  activeInfo => {
    logStatus(
      `Tab activated: ${activeInfo.tabId}.`
    );

    void reportActiveDomain(
      "tab-activated"
    );
  }
);


chrome.tabs.onUpdated.addListener(
  (
    tabId,
    changeInfo,
    tab
  ) => {
    if (
      !tab.active
    ) {
      return;
    }

    if (
      typeof changeInfo.url === "string"
    ) {
      logStatus(
        `Active tab navigation detected: ${tabId}.`
      );

      void reportActiveDomain(
        "tab-url-changed"
      );

      return;
    }

    if (
      changeInfo.status === "complete"
    ) {
      logStatus(
        `Active tab completed: ${tabId}.`
      );

      void reportActiveDomain(
        "tab-complete"
      );
    }
  }
);


chrome.windows.onFocusChanged.addListener(
  windowId => {
    if (
      windowId ===
      chrome.windows.WINDOW_ID_NONE
    ) {
      return;
    }

    logStatus(
      `Browser window focused: ${windowId}.`
    );

    void reportActiveDomain(
      "window-focus"
    );
  }
);


chrome.action.onClicked.addListener(
  tab => {
    logStatus(
      `Extension icon clicked on tab ${tab.id ?? "unknown"}.`
    );

    void reportActiveDomain(
      "action-click"
    );
  }
);


void ensureAlarm();

void reportActiveDomain(
  "service-worker-start"
);