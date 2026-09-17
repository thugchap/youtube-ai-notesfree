
import "./globals.css";

export const metadata = {
  title: "YouTube AI Notes",
  description: "YouTube videos to AI notes PDF",
};

export default function RootLayout({ children }) {
  return (
    <html lang="hi">
      <body>{children}</body>
    </html>
  );
}
