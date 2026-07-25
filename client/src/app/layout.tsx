import type { Metadata } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { AuthBootstrap } from "@/components/auth/AuthBootstrap"
import { QueryProvider } from "@/components/providers/QueryProvider"
import "./globals.css"

const geistSans = Geist({
  variable: "--font-sans",
  subsets: ["latin"],
})

const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
})

export const metadata: Metadata = {
  title: "Void Loop",
  description: "Habits, tasks, and notes — your daily loop.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="flex min-h-full flex-col bg-background text-foreground">
        <QueryProvider>
          <AuthBootstrap />
          {children}
        </QueryProvider>
      </body>
    </html>
  )
}
