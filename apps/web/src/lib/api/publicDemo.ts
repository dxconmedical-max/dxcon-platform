import { apiRequest } from "@/services/api";

export type DemoRequestBody = {
  full_name: string;
  organization?: string;
  email: string;
  phone?: string;
  message?: string;
  lang: "vi" | "en";
  consent_contact: boolean;
  /** Honeypot — must stay empty for real people. */
  website?: string;
};

/** Anonymous POST from the landing page "Book a demo" form. */
export async function submitDemoRequest(body: DemoRequestBody): Promise<{ reference: string }> {
  const response = await apiRequest<{ success: boolean; data: { reference: string } }>(
    "/api/v1/public/demo-requests",
    { method: "POST", body, timeoutMs: 30_000 },
  );
  return response.data;
}
