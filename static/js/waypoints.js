$(document).ready(function() {

	$('.wp1').waypoint(function() {
		console.log('waypoint');
        $('.wp1').addClass('animate__animated animate__fadeIn')

        /*
        $('#site-info1').addClass('animate__animated animate__pulse animate__delay-0.5s')
        $('#site-info2').addClass('animate__animated animate__pulse animate__delay-1s')
        $('#site-info3').addClass('animate__animated animate__pulse animate__delay-2s')
        */
	},
    {
		offset: '60%'
	})

});
    