export const config = {
  sentryEnabled: import.meta.env.VITE_SENTRY_ENABLED === "true",
  sentryBaseUrl: import.meta.env.VITE_SENTRY_BASE_URL ?? "http://localhost:8090",
};

export const isSentryEnabled = () => config.sentryEnabled;
