const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://kulima-os-backend.onrender.com/api/v1";

export async function getSummary(zone: string) {
  const res = await fetch(`${BASE_URL}/summary/${zone}`);
  return res.json();
}

export async function createSignal(data: any) {
  const res = await fetch(`${BASE_URL}/signal`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function generateReport(zone: string) {
  const res = await fetch(`${BASE_URL}/generate-prospectus`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ zone })
  });
  return res.json();
}
