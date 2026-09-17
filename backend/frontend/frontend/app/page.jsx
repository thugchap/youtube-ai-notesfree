
"use client";

import { useState } from "react";

export default function Home() {
  const [url, setUrl] = useState("");

  return (
    <main>
      <h1>YouTube AI Notes</h1>

      <p>YouTube वीडियो के नोट्स PDF में बनाओ</p>

      <input
        placeholder="YouTube वीडियो लिंक डालें"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />

      <button onClick={() => alert(url)}>
        Generate Notes PDF
      </button>
    </main>
  );
}
