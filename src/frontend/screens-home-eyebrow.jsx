/* global React */

function HomeEyebrow() {
  return (
    <div className="home-eyebrow">
      <div className="home-eyebrow__inner">
        <span className="home-eyebrow__mark">§ BEFORE THE READING</span>
        <span className="home-eyebrow__salawat" dir="rtl" lang="ar">
          اللهم صل على محمد وآل محمد
        </span>
      </div>
    </div>
  );
}

window.SOL_COMPS = window.SOL_COMPS || {};
window.SOL_COMPS.HomeEyebrow = HomeEyebrow;
