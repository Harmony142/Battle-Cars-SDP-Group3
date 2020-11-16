
import React from "react";

// reactstrap components

// core components
import IndexHeader from "components/Headers/IndexHeader.js";


function Index() {
  document.documentElement.classList.remove("nav-open");
  React.useEffect(() => {
    document.body.classList.add("index");
    return function cleanup() {
      document.body.classList.remove("index");
    };
  });
  return (
    <>
      <IndexHeader />
      <div className="main">
      </div>
    </>
  );
}

export default Index;
