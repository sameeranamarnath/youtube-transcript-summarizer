import "./globals.css";
import Navbar from "./Navbar";
import Header from "./Header";
import { sourceCodePro } from "./styles/fonts";;

export const metadata = {
  title: "Langchain based youtube QA bot",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${sourceCodePro.className}`}>
        <Header />
        <main className="flex flex-col pt-20 px-20">{children}</main>
      </body>
    </html>
  );
}
