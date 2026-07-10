import { Mail, MapPin, Phone } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";

export function ContactSection() {
  return (
    <section id="contact" className="bg-slate-50 px-4 py-20 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-2">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            Contact
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">
            Book a demo with our team
          </h2>
          <p className="mt-4 text-slate-600">
            Tell us about your lab or clinic network. We will schedule a
            walkthrough of DxCon workspaces and integrations.
          </p>
          <div className="mt-8 space-y-4 text-sm text-slate-600">
            <p className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-teal-600" />
              sales@dxcon.com.vn
            </p>
            <p className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-teal-600" />
              +84 (placeholder)
            </p>
            <p className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-teal-600" />
              Ho Chi Minh City, Vietnam
            </p>
          </div>
        </div>
        <form className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" placeholder="Your name" />
            </div>
            <div>
              <Label htmlFor="organization">Organization</Label>
              <Input id="organization" name="organization" placeholder="Clinic / Lab" />
            </div>
          </div>
          <div className="mt-4">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" name="email" type="email" placeholder="you@company.com" />
          </div>
          <div className="mt-4">
            <Label htmlFor="message">Message</Label>
            <textarea
              id="message"
              name="message"
              rows={4}
              placeholder="Tell us about your use case"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
            />
          </div>
          <Button type="button" className="mt-6 w-full">
            Send inquiry
          </Button>
        </form>
      </div>
    </section>
  );
}
