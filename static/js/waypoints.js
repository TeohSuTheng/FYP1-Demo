$(document).ready(function() {

	$('.wp1').waypoint(function() {
		console.log('waypoint');
        $('.wp1').addClass('animate__animated animate__fadeIn')
	},
    {
		offset: '75%'
	})

  $('.wp2').waypoint(function() {
		console.log('waypoint2');
        $('.wp2').addClass('animate__animated animate__fadeIn')
	},
    {
		offset: '75%'
	})

  $('.wp3').waypoint(function() {
		console.log('waypoint3');
        $('.wp3').addClass('animate__animated animate__fadeIn')
	},
    {
		offset: '75%'
	})

});
    