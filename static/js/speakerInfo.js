$(document).ready(function(){
//     $('input[type="checkbox"]').change(function() {
//     alert ("The element with id " + this.name + " changed.");
// });
    $(".copy").change(function() {

    // id = $(this).val();
    id = this.name
    console.log($(this))
    console.log(id)
    if ($(this).is(":checked")) {
	previd = id-1;
	$("#name"+id).val($("#name"+previd).val());

    var radio = $("M0")
    var selected_val = align.elements["sex"+previd].value
    var radios = align.elements["sex"+id]
    for (i=0;i<radios.length;i++) {
      if(radios[i].value == selected_val) {
        // console.log(radios[i].value)
        // console.log("hooray")
        // console.log(radios[i].id)
        // radios[i].checked = true;
        $("#"+radios[i].id).prop('checked', true);
      }
    }
    }
    else { //remove
	$("#name"+id).val("");

	$("#M"+id).prop('checked', false);
	$("#F"+id).prop('checked', false);
    $("#C"+id).prop('checked', false);
    // $("#sex"+id).val("");
   
    }
  })
})
