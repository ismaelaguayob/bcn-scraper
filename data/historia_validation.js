/*
 * JSTREE
 */
$(function() {
	$("#arbol").jstree({
		"checkbox": {
			"keep_selected_style": false,
			"three_state": false,
			"cascade": false
			
				},
		"plugins": ["checkbox"]
	});
	 $("#arbol").jstree("open_all");
});

//codigo para mantener flotante el arbol de navegacion
if($("#flotante").length > 0){
	$("#flotante").css('z-index',1);
	var ftop = $("#flotante").offset().top;
	$( window ).scroll(function() {
		if($(window).scrollTop() > ftop){
			$("#flotante").offset({ top: $(window).scrollTop(), left: $("#delimitador").offset().left });
		}else{
			$("#flotante").css('top','0px');
		}

	});
	var elFrame = $("#frame")[0];
	$(elFrame.contentWindow).resize(function() {
		$(window).trigger('zoom');
	});
	$(window).on('zoom', function() {
		if($("#flotante").length > 0){
			$("#flotante").offset({ top: ftop, left: $("#delimitador").offset().left });
		}
	});
}

$('#arbol').on('changed.jstree', function(e, data) {

	/**
	 * Dejar seleccionado sobre el checkbox
	 */
	if(data.node.state.selected === true){
		/**
		 * Nodo raíz
		 */
		if(data.node.parent == '#'){

			/**
			 * Abre todos los subnodos del arbol
			 */
			$('div.panel-collapse').each(function a (){
	//		$(this).collapse('show');
		//	$('#arbol').jstree('open_all');
			});
		}

		/**
		 * Tramite constitucional 
		 */
		else if(data.node.parent == 'raiz'){
			/**
			 * Abre todos los subnodos del tramite
			 */
			numero = data.node.id;
			$('#arbol').jstree('open_node',numero);
			numero = numero.split('_')[1];
			$('#collapse'+numero).collapse('show');
//			$('#collapse'+numero+' div.panel-collapse').collapse('show');
		}
		/**
		 * Nodo nivel documento
		 */
		else{
			numero = data.node.id;
			id = numero.split('_')[1];
			num = numero.split('_')[3];
			$('#collapse'+id).collapse('show');
			$('#collapse'+id+'_subacordeon'+num).collapse('show');
		}
	}else{ /** deseleccionar el checlbox **/
	
		/**
		 * deseleccionar la raiz
		 */
		if(data.node.parent == '#'){
			$('div.panel-collapse').each(function a (){
			//	$(this).collapse('hide');
			//	$('#arbol').jstree('close_all');
			});
		}
		/**
		 * deseleccionar trámite const
		 */
		else if(data.node.parent == 'raiz'){
			numero = data.node.id;
			$('#arbol').jstree('close_node',numero);
			numero = numero.split('_')[1];
			$('#collapse'+numero).collapse('hide');
//			$('#collapse'+numero+' div.panel-collapse').collapse('hide');
		}
		/**
		 * deseleccionar documento
		 */
		else{
			if(data.selected.length < 1){
				numero = data.node.id;
				id = numero.split('_')[1];
				num = numero.split('_')[3];
				$('#collapse'+id+'_subacordeon'+num).collapse('hide');
			}else{
				numero = data.node.id;
				id = numero.split('_')[1];
				num = numero.split('_')[3];
				$('#collapse'+id+'_subacordeon'+num).collapse('hide');
			}
		}
	}
});
$( document ).ready(function() {
	count0 = 0;
	count1 = 1;
	javascript = "";
	
	var collection = $('.principal');
	collection.each(function() {
		classa = collection[count0].id;
		javascript +="$('#"+classa+"').click(function() { " +
		"if($('#collapse"+count1+"').hasClass('collapse')){"+
		"$('#arbol').jstree('select_node', 'nodo_"+count1+"');"+
		"$('#arbol').jstree('open_node', 'nodo_"+count1+"'); "+
		"}"+
		"else if($('#collapse"+count1+"').hasClass('in')){"+
		"$('#arbol').jstree('deselect_node', 'nodo_"+count1+"');"+
		"$('#arbol').jstree('close_node', 'nodo_"+count1+"');"+
		"}"+	
		"});";
		count0++;
		count1++;
	});
	count0= 0;
	var collection = $('.sub');
	collection.each(function() {
		classa = collection[count0].id;
		classux = classa.split('_');
		javascript +="$('#"+classa+"').click(function() { "+
		"if($('#collapse"+classux[1]+"_subacordeon"+classux[2]+"').hasClass('collapse')){"+
		"$('#arbol').jstree('select_node', 'sub_"+classux[1]+"_nodo_"+classux[2]+"');"+
		"}else if($('#collapse"+classux[1]+"_subacordeon"+classux[2]+"').hasClass('in')){"+
		"$('#arbol').jstree('deselect_node', 'sub_"+classux[1]+"_nodo_"+classux[2]+"');"+
		"}"+
		"});";
		count0++;
	});
	count = 0;
	collection = $.each( $("div[id^='boton_']"), function () {
		classa = $(this).attr('id');
		classaux = classa.split('_');
		if(classaux.length < 3){
			javascript += "$('#"+classa+"').click(function() { "+
			"if(!$('#"+classa+"').hasClass('open')){"+
			"$('#collapse"+classaux[1]+"').css('min-height','200px');"+
			"$('#collapse"+classaux[1]+"').collapse('show');"+
			"}else {"+
			"$('#collapse"+classaux[1]+"').css('min-height','');"+
			"}"+
			"});";
		}else{
			javascript += "$('#"+classa+"').click(function() { "+
			"if(!$('#"+classa+"').hasClass('open')){"+
			"$('#collapse"+classaux[1]+"').collapse('show');"+
			"$('#collapse"+classaux[1]+"_subacordeon"+classaux[2]+"').css('min-height','200px');"+
			"$('#collapse"+classaux[1]+"_subacordeon"+classaux[2]+"').collapse('show');"+
			"} else {"+
			"$('#collapse"+classaux[1]+"_subacordeon"+classaux[2]+"').css('min-height','')"+
			"}"+
			"});";
		}
	});
	var script = document.createElement('script');
	script.type  = "text/javascript";
	script.text	 = javascript;
	document.getElementsByTagName('head')[0].appendChild(script);

	dondeEstoy(1);

});
function findElementByText(){
	text = $('.col-sm-5 .typeahead').val();
	var newtext = text.replace(/\s/g,"");
	$('.panel-body p', document.body).each(function(){
		$(this).html($(this).html().replace(
				new RegExp('<span class="destacar">', 'g'), ''
		));
	});
	if(text != '' && text.length >2){
		if($(".panel-body p:containsIN("+text+")").parent().parent().parent().parent().parent().parent().length > 0){
			$(".panel-body p:containsIN("+text+")").parent().parent().parent().parent().parent().parent().collapse('show');
		}else{
			$(".panel-body p").parent().parent().collapse('hide');
		}
		if($(".panel-body p:containsIN("+text+")").parent().parent()){
			$(".panel-body p:containsIN("+text+")").parent().parent().collapse('show');
		}else{
			$(".panel-body p").parent().parent().collapse('hide');
		}
		$('.panel-body p:containsIN('+text+')', document.body).each(function(){
			$(this).html($(this).html().replace(
					new RegExp(text, 'gi'), '<span class="destacar">$&</span>'
			));
		});
	}else{
		if($('.jstree-clicked').length>0){
			$('.jstree-clicked').each(function(){
				$('#'+$(this).attr('href').split('#')[1]).collapse('show');
			});
		}
		$('.jstree-anchor.jstree-clicked').each(function(){
			colapse = $(this).attr('href').split('#')[1];
			colprin = colapse.split('_')[0];
			$('#'+colprin).collapse('show');
			$('#'+colapse).collapse('show');

		});
	}
}
$.extend($.expr[":"], {
	"containsIN": function(elem, i, match, array) {
		return (elem.textContent || elem.innerText || "").toLowerCase().indexOf((match[3] || "").toLowerCase()) >= 0;
	}
});


function dondeEstoy(op){
	if(op == 1 &&  $('#esdossier').length>0){
		if($('#esdossier').val() == 0){
			$('.breadcrumb li:eq(1)').attr("title",$('#titulo').val());
			$('.breadcrumb li:eq(1)').text($('#titulo').val());
		}else{
			$('.breadcrumb li:eq(1)').remove();
			$('.breadcrumb li:eq(1)').remove();
			$('.breadcrumb li:eq(1)').attr("title",$('#titulo').val()+' Dossier personalizado');
			$('.breadcrumb li:eq(1)').text($('#titulo').val()+' Dossier personalizado');
		}
	}
}
$('.btn-enviar-seleccion').click(
		function(){
			var seleccionados= $("#arbol").jstree("get_selected");
			alertaDescarga('Preparando archivos para enviar a mi selección...','');
			bcn_herrAgregarMaletinIND(seleccionados);
			console.log(seleccionados);
		}
)

function herrPersonalizarDossier(op){bcn_herrPersonalizarDossier(op);}

