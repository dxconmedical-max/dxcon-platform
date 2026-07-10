export const metadata = { title: "Provider profile" };

export default async function ProviderProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-xl font-bold">Provider {id}</h1>
      <p className="text-sm text-slate-600">Public profile from marketplace API</p>
    </div>
  );
}
