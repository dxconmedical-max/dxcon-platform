export default function MarketplacePaymentPage() {
  const status = "PENDING";

  return (
    <div className="mx-auto max-w-md px-4 py-8 text-center">
      <h1 className="text-xl font-bold">Scan QR to pay</h1>
      <div className="mx-auto mt-6 flex h-48 w-48 items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-white">
        <span className="text-xs text-slate-500">QR payload from server</span>
      </div>
      <p className="mt-4 text-sm text-slate-600">Status: {status} (server-authoritative polling)</p>
    </div>
  );
}
