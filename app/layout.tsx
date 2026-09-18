import type { Metadata } from "next";
import { Inter, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "@/lib/theme";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Communication Overload Management",
  description: "AI-first communication triage — read everything, surface what matters.",
};

/* Applies the saved theme before first paint to avoid a flash.
   Defaults to the system preference when nothing is stored. */
const themeScript = `(function(){try{var t=localStorage.getItem("theme");var d=document.documentElement;var dark=false;if(t==="dark"){dark=true}else if(t==="light"){dark=false}else{dark=window.matchMedia("(prefers-color-scheme: dark)").matches}if(dark){d.classList.add("dark")}else{d.classList.remove("dark")}}catch(e){}})()`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script
          dangerouslySetInnerHTML={{ __html: themeScript }}
          suppressHydrationWarning
        />
      </head>
      <body className="min-h-full bg-background text-foreground font-sans">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}