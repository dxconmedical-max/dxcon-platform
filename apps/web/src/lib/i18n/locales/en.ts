export type MessageTree = {
  [key: string]: string | MessageTree;
};

export const en: MessageTree = {
  nav: {
    services: "Services",
    ai: "AI",
    partners: "Partners",
    pricing: "Pricing",
    contact: "Contact",
    signIn: "Sign in",
    bookDemo: "Book demo",
  },
  hero: {
    badge: "Healthcare diagnostics platform",
    title: "Connect labs, clinics, and patients on one trusted platform",
    subtitle:
      "DxCon unifies orders, home collection, lab operations, and clinical reporting with enterprise-grade security and AI-assisted insights.",
    contactSales: "Contact sales",
    previewLabel: "Illustrative platform preview",
    previewNote:
      "Capability overview for evaluation. Operational metrics are available inside authenticated workspaces.",
    trust: {
      security: "Security-first architecture",
      rbac: "Role-based access",
      audit: "Audit-ready workflows",
      ai: "AI-assisted insights subject to human review",
    },
    card: {
      orders: {
        title: "Order orchestration",
        text: "Reception-to-lab workflows with barcode and payment tracking.",
      },
      ai: {
        title: "Clinical decision support",
        text: "Advisory insights with mandatory clinician review.",
      },
      partners: {
        title: "Partner network",
        text: "Multi-tenant governance for labs, clinics, and hospital groups.",
      },
      security: {
        title: "Tenant isolation",
        text: "Organization-scoped access with audit trails.",
      },
    },
  },
  footer: {
    tagline: "Connected diagnostics for modern healthcare.",
    privacy: "Privacy",
    terms: "Terms",
  },
  bookDemo: {
    title: "Book a demo",
    subtitle: "Tell us about your organization and we will schedule a guided walkthrough.",
    submit: "Request demo",
  },
  contact: {
    title: "Contact sales",
    subtitle: "Reach the DxCon team for partnerships, pilots, and enterprise onboarding.",
  },
};
