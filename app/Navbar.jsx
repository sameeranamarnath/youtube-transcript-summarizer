"use client";

import React, { useEffect, useState } from "react";

import Link from "next/link";
import { sourceCodePro } from "./styles/fonts";
const Navbar = () => {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // const Navbar = () => {
  return (
    <nav className="fixed z-10 top-0 bg-gray-50 text-gray-800 w-full p-4 grid grid-cols-3 items-center">
      <a href="/" className={`text-center`}>
         Chat with a youtube video Using GenAI-Amar.S 
      </a>
      {/* Render HamburgerMenu component on the client side */}
      <div className="hidden">
          </div>
    </nav>
  );
};

export default Navbar;
