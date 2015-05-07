$(document).ready(function(){
    $(".copy").change(function() {
    id = $(this).val();
    if ($(this).is(":checked")) {
	previd = id-1;
	$("#name"+id).val($("#name"+previd).val());
	if ($("#msex"+previd).is(":checked")) { $("#msex"+id).prop('checked', true); }
	else if ($("#fsex"+previd).is(":checked")) { $("#fsex"+id).prop('checked', true); }
    }
    else {
	$("#name"+id).val("");
	$("#msex"+id).prop('checked', false);
	$("#fsex"+id).prop('checked', false);
    }
  })
})
