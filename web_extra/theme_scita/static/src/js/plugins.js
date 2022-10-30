/*global $*/
$(document).ready(function () {

    "use strict";

    $("header .top-header .color-gray").on("click", function () {
       $("body").toggleClass("site-gray");
    });

    $("html body #wrapwrap.homepage .our-rules-page .item").hover( function () {
        $(this).find("p").slideDown();
    }, function () {
        $(this).find("p").slideUp();
    });

    $(".sustainability .options .option").click(function () {
        $(this).addClass("active").siblings().removeClass("active");
    });
    $(".sustainability .options .option").hover(function () {
        $(this).addClass("active").siblings().removeClass("active");
    });

    // Search Validation
    var validateSearch = function(){
        var query = $("#txtSearchTerm").val();
        var mobilequery = $("#mobile-txtSearchTerm").val();
        if(query && query !=''){
            document.location.href = '/search-results?q='+query;
        }else{
            console.log("ERROR");
        }
        if(mobilequery && mobilequery !=''){
            document.location.href = '/search-results?q='+mobilequery;
        }else{
            console.log("ERROR");
        }
    }
    $('#btnSearch').click(function(){
        validateSearch();
    });
    $('#txtSearchTerm').keyup(function(e){
        if(e.keyCode == 13){
            validateSearch();
        }
    });
    $("#btnSearchIconHead").click(()=>{
        $('#txtSearchTerm').focus();
    });
});

// On page load set the theme.
(function() {
  let onpageLoad = localStorage.getItem("theme") || "light";
  let element = document.body;
  if(element && onpageLoad){
     element.classList.toggle(onpageLoad);
     document.getElementById("theme").textContent = localStorage.getItem("theme") || "light";
  }

})();

function themeToggle() {
  let element = document.body;
  element.classList.toggle("site-dark");

  let theme = localStorage.getItem("theme");
  if (theme && theme === "site-dark") {
    localStorage.setItem("theme", "light");
  } else {
    localStorage.setItem("theme", "site-dark");
  }

  document.getElementById("theme").textContent = localStorage.getItem("theme");
}