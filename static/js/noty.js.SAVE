function createNoty(message, type) {
    var html = '<div class="alert alert-' + type + ' alert-dismissable page-alert">';
    html += '<button type="button" class="close"><span aria-hidden="true">×</span><span class="sr-only">Close</span></button>';
    html += message;
    html += '</div>';
    $(html).hide().prependTo('#noty-holder').slideDown();
};

$(function(){
    createNoty('We have recently upgraded the site to use the Montreal Forced Aligner instead of ProsodyLab Aligner. This may result in differences -- we hope for the better! -- on the alignments and eventual vowel formants. The upgrade also includes a few other useful features. <a href="http://darla.dartmouth.edu:8080/main.py/">Click here if you prefer to use the system with the old aligner.</a>', 'danger');
    $('.page-alert .close').click(function(e) {
        e.preventDefault();
        $(this).closest('.page-alert').slideUp();
    });
});
