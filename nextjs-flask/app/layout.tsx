import { Toaster } from "@/components/ui/sonner";
import "./globals.css";
import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Nephased",
  description: "Demo for Nepali Hate Sentiment Detection",
  keywords: [
    "Machine Learning",
    "ML/AI",
    "AI",
    "Data Science",
    "Sentiment Detection",
    "Hate Sentiment",
    "BERT",
    "Classifcation",
    "Nephased",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
