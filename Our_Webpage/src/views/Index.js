
import React from "react";

// reactstrap components

// core components
import IndexHeader from "components/Headers/IndexHeader.js";

// index sections
import SectionButtons from "views/index-sections/SectionButtons.js";
import SectionNavbars from "views/index-sections/SectionNavbars.js";
import SectionProgress from "views/index-sections/SectionProgress.js";
import SectionJavaScript from "views/index-sections/SectionJavaScript.js";

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
        {/* <SectionButtons />
        <SectionNavbars />
        <SectionProgress />
        <SectionJavaScript /> */}
      </div>
    </>
  );
}

export default Index;
