var n=document.createElement("div");n.className="hidden d-none";document.head.appendChild(n);var e=window.getComputedStyle(n).display==="none";document.head.removeChild(n);if(!e){var o=document.createElement("link");o.href="/css/bootstrap.min.css";o.rel="stylesheet";document.head.appendChild(o)}var t=document.createElement("span");t.className="fa";t.style="display:none";document.head.appendChild(t);var d=window.getComputedStyle(t,null).getPropertyValue("font-family")=='"Font Awesome 5 Pro"';document.head.removeChild(t);if(!d){var o=document.createElement("link");o.href="/css/all.min.css";o.rel="stylesheet";document.head.appendChild(o)}