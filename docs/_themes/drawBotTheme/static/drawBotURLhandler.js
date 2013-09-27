$(document).ready(function () {
	$(".drawbotlink").each(function () {
		this.protocol = "drawbot";
	});

	$('img').wrap(function() {
    	return $('<a>', {
        	href: $(this).attr('src'),
        	rel: 'lightbox-drawbot'
    	});
	});
});