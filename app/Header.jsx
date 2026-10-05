import React from "react";
import { sourceCodePro } from "./styles/fonts";

const Header = ({header}) => {
  const year = new Date().getFullYear();
  return (
    <header
      className={`p-4 bg-gray-800 text-white w-full grid grid-cols-3 fixed  ${sourceCodePro.className}`}
    >
      <p className={`text-center ${sourceCodePro.className}`}>
      {header? header:"Youtube video based summarisation & QA bot"}
      </p>
    </header>
  );
};

export default Header;
