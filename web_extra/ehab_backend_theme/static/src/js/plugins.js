function toggleClassName(elem)
{
    var sidbarIcon = document.querySelectorAll(".oe_favorite_menu .oe_apps_menu > .o_app");
    for (i=0; i < sidbarIcon.length; i++)
    {
        sidbarIcon[i].classList.remove("active")
    }
    elem.classList.add("active");
}

/*global $
$(document).on("DOMSubtreeModified", function () {
    "use strict";
    $(".o_thread_message_avatar").parents(".o_mail_discussion").addClass("internal");
    $(".internal, .o_thread_date_separator").prev().addClass("last");
});
*/