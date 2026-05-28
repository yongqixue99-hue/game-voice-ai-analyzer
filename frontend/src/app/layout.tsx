import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "游戏语音 AI 分析工具",
  description: "离线上传游戏语音录音并在网页中回放。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
