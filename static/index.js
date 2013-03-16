$(function(){
    $("#groupslist > li").click(function(event){
        var group = this.firstChild.getAttribute("href").slice(1);
        $("#subjectslist").html("");
        event.preventDefault();
        $.ajax({
            url: group,
        }).done(function(html) {
            $("#subjectslist").html(html);
            $("#subjectslist > li").click(function(event){
                event.preventDefault();
                $.ajax({
                    url: group+'/'+($(this).data('num')),
                }).done(function(html) {
                    $('#message').html(html);
                });
            });
        });
    });
})
