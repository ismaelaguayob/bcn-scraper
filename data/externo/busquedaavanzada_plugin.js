/*$('.datepicker').datepicker(
        {
            format: 'dd/mm/yyyy',
            weekStart: 1,
            language: "es",
            keyboardNavigation: true,
            todayBtn: 'linked'
        }
);*/
$(function($){
    $.datepicker.regional['es'] = {
        closeText: 'Cerrar',
        prevText: '<Ant',
        nextText: 'Sig>',
        currentText: 'Hoy',
        monthNames: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
        monthNamesShort: ['Ene','Feb','Mar','Abr', 'May','Jun','Jul','Ago','Sep', 'Oct','Nov','Dic'],
        dayNames: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'],
        dayNamesShort: ['Dom','Lun','Mar','Mié','Juv','Vie','Sáb'],
        dayNamesMin: ['Do','Lu','Ma','Mi','Ju','Vi','Sá'],
        weekHeader: 'Sm',
        dateFormat: 'dd/mm/yy',
        firstDay: 1,
        isRTL: false,
        showMonthAfterYear: false,
        yearSuffix: ''
    };
    $.datepicker.setDefaults($.datepicker.regional['es']);
});
function mostrar_campo_fecha(dom) {
    $(dom).closest('.form-group').next().find('.busqueda_fecha').show();
    $(dom).closest('.form-group').next().find('.busqueda_fecha').find("input[type=text]").each(function(){  $(this).prop("required", true); });
    $(dom).closest('.form-group').next().find('.busqueda_normal').hide();
    $(dom).closest('.form-group').next().find('.busqueda_normal').find("input[type=text]").each(function(){  $(this).removeAttr("required"); });
    var tmp = $(dom).closest('.form-group').next().find('.busqueda_normal').find("input");
    if (tmp.length === 2){
        tmp.filter(".typeahead").typeahead("destroy");
        tmp.filter(".typeahead").removeClass (function (index, css) {
            return (css.match (/\bsugerencia-topico-\S+/g) || []).join(' ');
        }).removeClass("typeahead");
    }

}

function validarpornumero(obj) {
    $(obj).closest('.form-group').next().find('.busqueda_normal').html('<div class="busqueda_normal" style="display:block"><div><label><input type="text" oninvalid="invalidMsg(this)" oninput="invalidMsg(this)" required="" class="form-control" placeholder=""></label></div></div>');
    var tmp = $(obj).closest('.form-group').next().find('.busqueda_normal').find("input");
    if (tmp.length === 1){
        tmp.removeClass();
        tmp.addClass("form-control validate-solonumeros");
    }
    else if (tmp.length === 2){
        tmp.filter(".typeahead").removeClass (function (index, css) {
            return (css.match (/\bvalidate-\S+/g) || []).join(' ');
        });
        tmp.filter(".typeahead").addClass("form-control validate-solonumeros");
    }
    validarSoloNumeros(".validate-solonumeros");
}

function validarporletrasysimbolos(obj) {
    $(obj).closest('.form-group').next().find('.busqueda_normal').html('<div class="busqueda_normal" style="display:block"><div><label><input type="text" required="" class="form-control" placeholder=""></label></div></div>');
    var tmp = $(obj).closest('.form-group').next().find('.busqueda_normal').find("input");
    if (tmp.length === 1){
        tmp.removeClass();
        tmp.addClass("form-control validate-letrasysimbolos");
    }
    else if (tmp.length === 2){
        tmp.filter(".typeahead").removeClass (function (index, css) {
            return (css.match (/\bvalidate-\S+/g) || []).join(' ');
        });
        tmp.filter(".typeahead").addClass("form-control validate-letrasysimbolos");
    }
    validarNoNumeros(".validate-letrasysimbolos");
}

function validarporletras_simbolos_numeros(obj) {
    $(obj).closest('.form-group').next().find('.busqueda_normal').html('<div class="busqueda_normal" style="display:block"><div><label><input type="text" required="" class="form-control" placeholder=""></label></div></div>');
    var tmp = $(obj).closest('.form-group').next().find('.busqueda_normal').find("input");
    if (tmp.length === 1){
        tmp.removeClass();
        tmp.addClass("form-control validate-letras_simbolos_numeros");
    }
    else if (tmp.length === 2){
        tmp.filter(".typeahead").removeClass (function (index, css) {
            return (css.match (/\bvalidate-\S+/g) || []).join(' ');
        });
        tmp.filter(".typeahead").addClass("form-control validate-letras_simbolos_numeros");
    }
    validarLetrasSimbolosNumeros(".validate-letras_simbolos_numeros");
}

function validarporletrasyespacios(obj){
    $(obj).closest('.form-group').next().find('.busqueda_normal').html('<div class="busqueda_normal" style="display:block"><div><label><input type="text" required="" class="form-control" placeholder=""></label></div></div>');
    var tmp = $(obj).closest('.form-group').next().find('.busqueda_normal').find("input");
    if (tmp.length === 1){
        tmp.removeClass();
        tmp.addClass("form-control validate-letrasyespacios");
    }
    else if (tmp.length === 2){
        tmp.filter(".typeahead").removeClass (function (index, css) {
            return (css.match (/\bvalidate-\S+/g) || []).join(' ');
        });
        tmp.filter(".typeahead").addClass("form-control validate-letrasyespacios");
    }
    validarSoloLetrasEspacios(".validate-letrasyespacios");
}

function ocultar_campo_fecha(dom) {
    $(dom).closest('.form-group').next().find('.busqueda_fecha').hide();
    $(dom).closest('.form-group').next().find('.busqueda_fecha').find("input[type=text]").each(function(){  $(this).removeAttr("required"); });
    $(dom).closest('.form-group').next().find('.busqueda_normal').show();
    $(dom).closest('.form-group').next().find('.busqueda_normal').find("input[type=text]").each(function(){  $(this).prop("required", true); });
}
/*
function limpiar_campos(obj){
    var html = '<div class="inner-box4">\n<div class="form-group">\n<div class="checkbox">\n<div>\n<label>\nBuscar por:\n<select class="form-control buscar_por" name="">\n<option value="numero" class="show_text">Número de Ley</option>\n<option value="articulo" class="show_text">Artículo (requiere número de ley)</option>\n<option value="frase" class="show_text">Palabra o frase</option>\n<option value="boletin" class="show_text">Número de Boletín</option>\n<option value="autor" class="show_text">Autor</option>\n<option value="fecha_publicacion" class="show_date">Fecha de publicación</option>\n<option value="camara_origen" class="show_text">Cámara de origen</option>\n<option value="comision" class="show_text">Comision</option>\n<option value="intervinente" class="show_text">Persona interviniente</option>\n<option value="fecha_inicio_tramite" class="show_date">Fecha de ingreso a trámite</option>\n<option value="acuerdos_internacionales" class="show_text">Acuerdos internacionales</option>\n<option value="mocion" class="show_text">Iniciativa (moción / mensaje)</option>\n<option value="ministerio" class="show_text">Ministerio</option>\n</select>\n</label>\n</div>\n</div>\n</div>\n<div class="form-group">\n<div class="busqueda_normal" style="display:block">\n<div><label><input type="text" required class="form-control" placeholder=""></label></div>\n</div>\n<div class="busqueda_fecha" style="display:none">\n<div> <label>De: <input type="text" class="datepicker fecha-inicio" required>&nbsp;</label> <label>&nbsp;&nbsp;&nbsp;&nbsp;A: <input type="text" class="datepicker fecha-fin" required></label> </div>\n</div>\n</div>\n<div class="form-group">\n<div class="checkbox">\n<div class="text-center"> <label> <input type="checkbox" name="excluir" value="1">&nbsp;&nbsp;Excluir </label> </div>\n</div>\n</div>\n<div class="form-group pull-right"> <a onclick="javascript:eliminarItem($(this))" title="Quitar Filtro"><img alt="Quitar Filtro" class="icono_menos" src="fileadmin/template/img/icons/32/menos.png"></a><br> <a onclick="javascript:agregarItem();"><img class="icono_mas" src="fileadmin/template/img/icons/32/mas.png" alt="Añadir filtro"></a> </div>\n</div>';
    obj.closest('div.box3.item-busqueda').html(html);
}
*/
function limpiar_campos(obj){
    obj.closest('.inner-box4').find("input.con_sugerencia").typeahead('destroy');
    obj.closest('.inner-box4').find(".checkbox:eq(1)").find("input[type=checkbox][name=excluir]").prop('checked', false);
    obj.closest('.inner-box4').find("input").each(function() {
        $(this).val("");
    });
}

function deshabilitarOtros(valor){
    var str = "numero;boletin;camara_origen;fecha_publicacion;fecha_inicio_tramite;acuerdos_internacionales;mocion";
    var existe = (jQuery.inArray(valor, str.split(";"))>-1) ? true:false;
    var cantidad_seleccionadas = $("select.buscar_por option:checked[value="+valor+"]").length;

    if (existe){
        $("select.buscar_por option:checked[value="+valor+"]:first").attr("disabled", false);
        //$("select.buscar_por option:checked[value="+valor+"]:first").css("display", "block");
        if (cantidad_seleccionadas >= 1){
            $("select.buscar_por option[value="+valor+"]:not(:first)").attr("disabled", true);
            //$("select.buscar_por option:checked[value="+valor+"]:first").css("display", "none");
        }else if (cantidad_seleccionadas === 0){
            $("select.buscar_por option[value="+valor+"]").attr("disabled", false);
        }
    }
}
function verificarSiDeshabilitar(){
    var str = "numero;boletin;camara_origen;fecha_publicacion;fecha_inicio_tramite;acuerdos_internacionales;mocion";
    var arreglo = str.split(";");
    $.each(arreglo, function( index, value ){
        deshabilitarOtros(value);
    });
}

function validarSoloNumeros(dom){
    var specialKeys = new Array();
    specialKeys.push(8); //Backspace
    $(function () {
        var handler = function (e) {
            var keyCode = e.which ? e.which : e.keyCode
            var ret = ((keyCode >= 48 && keyCode <= 57) || specialKeys.indexOf(keyCode) != -1 || e.which == 13);
            if (!ret){
                alerta("Sólo se permite el ingreso de números");
            }
            return ret;
       }
       $(dom).unbind("keypress");
       $(dom).bind("keypress", handler);
       $(dom).bind("paste", function (e) {
            return false;
       });
       $(dom).bind("drop", function (e) {
            return false;
       });
    });
}

function validarNoNumeros(dom){
    var specialKeys = new Array();
    specialKeys.push(8); //Backspace

    $(function () {
        var handler = function (e) {
            var keyCode = e.which ? e.which : e.keyCode
            var ret = ((keyCode < 48 || keyCode > 57) || specialKeys.indexOf(keyCode) != -1);
            $(".error").css("display", ret ? "none" : "inline");
            if (!ret){
                alerta("No se permite el ingreso de números");
            }
            return ret;
        }
        $(dom).unbind("keypress");
        $(dom).bind("keypress", handler);
        $(dom).bind("paste", function (e) {
            return false;
        });
        $(dom).bind("drop", function (e) {
            return false;
        });
    });
}

function validarLetrasSimbolosNumeros(dom){
    var specialKeys = new Array();
    specialKeys.push(8); //Backspace

    $(function () {
        var handler = function (e) {
            var keyCode = e.which ? e.which : e.keyCode
            //var ret = ((keyCode >= 48 && keyCode <= 57) || specialKeys.indexOf(keyCode) != -1);
            /*if (!ret){
                alerta("Sólo se permite el ingreso de números");
            }*/
            //return ret;
            return true;
        }
        $(dom).unbind("keypress");
        $(dom).bind("keypress", handler);
        $(dom).bind("paste", function (e) {
            return false;
        });
        $(dom).bind("drop", function (e) {
            return false;
        });
    });
}


function validarSoloLetrasEspacios(dom){

    var whitelist = "á,é,í,ó,ú,a,b,c,d,e,f,g,h,i,j,k,l,m,n,ñ,o,p,q,r,s,t,u,v,w,x,y,z,Á,É,Í,Ó,Ú,A,B,C,D,E,F,G,H,I,J,K,L,M,N,Ñ,O,P,Q,R,S,T,U,V,W,X,Y,Z, ".split(',');

    var handler = function (e) {
        var keyCode = e.which ? e.which : e.keyCode
        var key = String.fromCharCode(keyCode);
        if (whitelist.indexOf(key)  === -1 ){
            alerta("No se permite el ingreso de números y simbolos");
            return false;
        }else{
            return true;
        }
    }

    $(dom).unbind("keypress");
    $(dom).bind("keypress", handler);
    $(dom).bind("paste", function (e) {
        return false;
    });
    $(dom).bind("drop", function (e) {
        return false;
    });
}



function actualizarItemsSelect(){
    $("select.buscar_por").change(function(event) {
        var obj = $(this);
        limpiar_campos(obj);
        $("option:selected", $(this)).each(function() {
            $(obj).unbind("keypress");
            if ($(this).hasClass("show_text")) {
                ocultar_campo_fecha(obj);
            }
            if ($(this).hasClass("show_date")) {
                mostrar_campo_fecha(obj);
            }
            switch ($(this).val()){
                case "numero":
                    validarpornumero(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-numeroley typeahead");
                    break;
                case "articulo":
                    validarporletras_simbolos_numeros(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-articulos typeahead");
                    break;
                case "frase":
                    validarporletras_simbolos_numeros(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-palabras_frases typeahead");
                    break;
                case "boletin":
                    validarporletras_simbolos_numeros(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-numero_boletines typeahead");
                    break;
                case "autor":
                    validarporletrasyespacios(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-autores typeahead");
                    break;
                case "fecha_publicacion":
                    break;
                case "camara_origen":
                    validarporletrasyespacios(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-camaras typeahead");
                    break;
                case "comision":
                    validarporletrasyespacios(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-comisiones typeahead");
                    break;
                case "intervinente":
                    validarporletrasyespacios(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-personas_intervienes typeahead");
                    break;
                case "fecha_inicio_tramite":
                    break;
                case "acuerdos_internacionales":
                    validarporletras_simbolos_numeros(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-acuerdos typeahead");
                    break;
                case "mocion":
                    validarporletrasysimbolos(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-iniciativas typeahead");
                    break;
                case "ministerio":
                    validarporletrasyespacios(obj);
                    $(obj).agregarClaseInput("sugerencia-topico-ministerio typeahead");
                    break;
            }
        });
        verificarSiDeshabilitar();
        sugerirTopico();
    });
}
function crearDialogosIntervaloFechas(){
    var startDate = new Date();
    var endDate = new Date();
    var conf =  {format: 'dd/mm/yyyy', weekStart: 1, language: "es", keyboardNavigation: true, todayBtn: 'linked' };
    $('.fecha-inicio:not(.con_calendario)').datepicker({format: 'dd/mm/yyyy', weekStart: 1, language: "es", keyboardNavigation: true, todayBtn: 'linked' }).on('changeDate', function(ev){
        if (ev.date.valueOf() > endDate.valueOf()){
            alerta('La fecha inicial no puede ser mayor que la fecha final');
        } else {
            startDate = new Date(ev.date);
        }
        $('.fecha-inicio').datepicker('hide');
/*    }).on("show", function(e){
        // `e` here contains the extra attributes
        $(this).addClass("activa");
        $(".datepicker:not(activa)").datepicker('hide');
        $(this).removeClass("activa");*/
    });
    $('.fecha-fin:not(.con_calendario)').datepicker({format: 'dd/mm/yyyy', weekStart: 1, language: "es", keyboardNavigation: true, todayBtn: 'linked' }).on('changeDate', function(ev){
        if (ev.date.valueOf() < startDate.valueOf()){
            alerta('La fecha final no puede ser menor que la fecha inicial');
        } else {
            endDate = new Date(ev.date);
        }
        $('.fecha-fin').datepicker('hide');
/*    }).on("show", function(e){
        // `e` here contains the extra attributes
        $(this).addClass("activa");
        $(".datepicker:not(activa)").datepicker('hide');
        $(this).removeClass("activa");*/
    });
    $(".datepicker").addClass("con_calendario");
}

function itemEstaHabilitado(name){
    return $("input.hidden[name=item_"+name+"]").val()=="true"?true:false;
}

function agregarItem(){
//    var html = '<div class="box3 item-busqueda">\n<div class="inner-box4">\n<div class="form-group">\n<div class="checkbox">\n<div>\n<label>\nBuscar por:\n<select class="form-control buscar_por" name="">\n<option value="numero" class="show_text">Número de Ley o Decreto</option>\n<option value="articulo" class="show_text">Artículo (requiere número de ley o decreto)</option>\n<option value="frase" class="show_text">Palabra o frase</option>\n<option value="boletin" class="show_text">Número de Boletín</option>\n<option value="autor" class="show_text">Autor</option>\n<option value="fecha_publicacion" class="show_date">Fecha de publicación</option>\n<option value="camara_origen" class="show_text">Cámara de origen</option>\n<option value="comision" class="show_text">Comision</option>\n<option value="intervinente" class="show_text">Persona interviniente</option>\n<option value="fecha_inicio_tramite" class="show_date">Fecha de ingreso a trámite</option>\n<option value="acuerdos_internacionales" class="show_text">Acuerdos internacionales</option>\n<option value="mocion" class="show_text">Iniciativa (moción / mensaje)</option>\n<option value="ministerio" class="show_text">Ministerio</option>\n</select>\n</label>\n</div>\n</div>\n</div>\n<div class="form-group">\n<div class="busqueda_normal" style="display:block">\n<div><label><input type="text" required class="form-control" placeholder=""></label></div>\n</div>\n<div class="busqueda_fecha" style="display:none">\n<div> <label>De: <input type="text" class="datepicker fecha-inicio" required>&nbsp;</label> <label>&nbsp;&nbsp;&nbsp;&nbsp;A: <input type="text" class="datepicker fecha-fin" required></label> </div>\n</div>\n</div>\n<div class="form-group">\n<div class="checkbox">\n<div class="text-center"> <label> <input type="checkbox" name="excluir" value="1">&nbsp;&nbsp;Excluir </label> </div>\n</div>\n</div>\n<div class="form-group pull-right"> <a onclick="javascript:eliminarItem($(this))" title="Quitar Filtro"><img alt="Quitar Filtro" class="icono_menos" src="fileadmin/template/img/icons/32/menos.png"></a><br> <a onclick="javascript:agregarItem();"><img class="icono_mas" src="fileadmin/template/img/icons/32/mas.png" alt="Añadir filtro"></a> </div>\n</div>\n</div>';
    var html = '<div class="box3 item-busqueda">\n<div class="inner-box4">\n<div class="form-group">\n<div class="checkbox">\n<div>\n<label>\nBuscar por:\n<select class="form-control buscar_por" name="">\n<option value="numero" class="show_text">Número de Ley o Decreto</option>\n<option value="articulo" class="show_text">Artículo (requiere número de ley o decreto)</option>\n<option value="frase" class="show_text">Palabra o frase</option>\n<option value="boletin" class="show_text">Número de Boletín</option>\n<option value="autor" class="show_text">Autor</option>\n<option value="fecha_publicacion" class="show_date">Fecha de publicación</option>\n<option value="camara_origen" class="show_text">Cámara de origen</option>\n<option value="comision" class="show_text">Comision</option>\n<option value="intervinente" class="show_text">Persona interviniente</option>\n<option value="fecha_inicio_tramite" class="show_date">Fecha de ingreso a trámite</option>\n<option value="mocion" class="show_text">Iniciativa (moción / mensaje)</option>\n<option value="ministerio" class="show_text">Ministerio</option>\n</select>\n</label>\n</div>\n</div>\n</div>\n<div class="form-group">\n<div class="busqueda_normal" style="display:block">\n<div><label><input type="text" required class="form-control" placeholder=""></label></div>\n</div>\n<div class="busqueda_fecha" style="display:none">\n<div> <label>De: <input type="text" class="datepicker fecha-inicio" required>&nbsp;</label> <label>&nbsp;&nbsp;&nbsp;&nbsp;A: <input type="text" class="datepicker fecha-fin" required></label> </div>\n</div>\n</div>\n<div class="form-group">\n<div class="checkbox">\n<div class="text-center"> <label> <input type="checkbox" name="excluir" value="1">&nbsp;&nbsp;Excluir </label> </div>\n</div>\n</div>\n<div class="form-group pull-right"> <a onclick="javascript:eliminarItem($(this))" title="Quitar Filtro"><img alt="Quitar Filtro" class="icono_menos" src="fileadmin/template/img/icons/32/menos.png"></a><br> <a onclick="javascript:agregarItem();"><img class="icono_mas" src="fileadmin/template/img/icons/32/mas.png" alt="Añadir filtro"></a> </div>\n</div>\n</div>';
      $(html).appendTo('.lista-busqueda');

    // si el item esta deshabilitado se elimina del select
    $(".lista-busqueda select.buscar_por:last option").each(function(i){
        if (!itemEstaHabilitado($(this).attr("value"))){
            $(".lista-busqueda select.buscar_por:last option[value="+$(this).attr("value")+"]").remove();

        }
    });

    validarpornumero("select.buscar_por:last");
    $("select.buscar_por:last option:selected").agregarClaseInput("sugerencia-topico-numeroley typeahead");
    verificarSiDeshabilitar();
    sugerirTopico();
    actualizarItemsSelect();
    crearDialogosIntervaloFechas();
    $("select.buscar_por:last option:selected").removeAttr("selected");
    ocultar_campo_fecha($("select.buscar_por:last option:first"));
    ocultarMenos();
    $("select.buscar_por:last").change();
}


$(function() {
    $("ol.breadcrumb li.active").removeClass("hidden");
    $('.busqueda_fecha').hide();
    $('select.buscar_por option').addClass("show_text");
    $('select.buscar_por option[value^="fecha"]').removeClass("show_text").addClass("show_date");
    agregarItem();
    $("form[name=newBusquedaAvanzada]").submit(function( event ) {
        var json = generarJsonInput();
        event.preventDefault();

        if (json === false){
            //event.preventDefault();
        }
        else{
            $("input#json").val(json);
            //$("form[name=newBusquedaAvanzada]").submit();
            bcn_verTextoCompleto(json);
        }
    });
});


function agregarItemInput(key, obj){
    var array = new Array();
    $("select.buscar_por option.show_text:selected[value='"+key+"']").closest('.form-group').next().find('.busqueda_normal').find("input").each(
        function(){
            var tmp = new Object();
            tmp.valor = $(this).val();
            tmp.excluye = $(this).closest('.inner-box4').find(".checkbox:eq(1)").find("input[type=checkbox][name=excluir]").is(":checked");
            array.push(tmp);
        }
    );
    $("select.buscar_por option.show_date:selected[value='"+key+"']").closest('.form-group').next().find('.busqueda_fecha').each(
        function(){
            var array_fechas = new Array();
            $(this).find("input").each(function(){
                var tmp = new Object();
                tmp.valor = $(this).val();
                tmp.excluye = $(this).closest('.inner-box4').find(".checkbox:eq(1)").find("input[type=checkbox][name=excluir]").is(":checked");
                array_fechas.push(tmp);
            });
            array.push(array_fechas);
        }
    );
    if (array.length > 0){
        obj[key] = array;
    }
    else{
        obj[key] = null;
    }
    return obj;
}

function eliminarItem(item){
    var cantidad_item_busqueda = $(".lista-busqueda .item-busqueda").length;
    var cantidad_nroley = $("select.buscar_por option:checked[value=numero]").length;
    var cantidad_nroarticulo = $("select.buscar_por option:checked[value=articulo]").length;

    //$(this).closest(".inner-box4").find("select.buscar_por option:checked[value=numero]").addClass("red");
    var quiereborrarnroley = item.closest(".inner-box4").find("select.buscar_por option[value=numero]").is(":checked");
    if (cantidad_item_busqueda < 2){
        alerta("Debe haber al menos un criterio de búsqueda");
    } else if ((cantidad_nroley == 1 ) && (cantidad_nroarticulo >= 1) &&  quiereborrarnroley){
        alerta("Para la búsqueda de “Número de Artículo” es necesario  el criterio de busqueda de “Número de Ley o Decreto”");
    } else{
        item.closest(".item-busqueda").detach();
    }
    verificarSiDeshabilitar();
    ocultarMenos();
}

function generarJsonInput(){

//    $("input.form-control.validate-letrasyespacios").attr("pattern", "[a-zA-Z\s]+");
//    $("input.form-control.validate-letrasysimbolos").attr("pattern", "[a-zA-Z\s]+");
//    $("input.form-control.validate-solonumeros").attr("pattern", "[0-9\s]+");


    // itera sobre el primer elemento y obtine todas los value, que se usaran para hacer las key del json
    var obj = new Object();
    var json = "";

    var cantidad_item_busqueda = $(".lista-busqueda .item-busqueda").length;
    var cantidad_excluyentes = $("input[name=excluir][type=checkbox]:checked").length;
    var cantidad_busqueda_por_articulo = $("select.buscar_por option.show_text:selected[value='articulo']").length;
    var cantidad_busqueda_por_numero = $("select.buscar_por option.show_text:selected[value='numero']").length;

    if (cantidad_item_busqueda < 1){
        alerta("Debe haber al menos un criterio de búsqueda");
        return false
    }else if (cantidad_excluyentes === 1 && cantidad_item_busqueda === 1){
        alerta ("Si es que existe un solo criterio de búsqueda, ésta  no puede ser excluyente");
        return false;
    }
    else if (cantidad_busqueda_por_numero === 0 && cantidad_busqueda_por_articulo > 0){
        alerta("Para la búsqueda de Número de Artículo es necesario agregar el criterio de Buscar por “Número de Ley o Decreto”");
        return false;
    }else{
        $("select.buscar_por:first option").each(
            function(){
                obj = agregarItemInput($(this).val(), obj)
            }
        );

        var array_fecha_publicacion = obj.fecha_publicacion;
        var array_fecha_inicio_tramite = obj.fecha_inicio_tramite;

        if(Object.prototype.toString.call(array_fecha_publicacion) === "[object Array]"){

            array_fecha_publicacion.forEach(function(item) {
                var fecha_inicial = parsearFechaDiaMesAño(item[0].valor);
                var fecha_final = parsearFechaDiaMesAño(item[1].valor);

                if (fecha_inicial>fecha_final){
                    alerta("En busqueda de fecha de publicación, la fecha inicial no puede ser mayor que la fecha final");
                    return false;
                }
            });
        }

        if(Object.prototype.toString.call(array_fecha_inicio_tramite) === "[object Array]"){
            array_fecha_inicio_tramite.forEach(function(item) {
                var fecha_inicial = parsearFechaDiaMesAño(item[0].valor);
                var fecha_final = parsearFechaDiaMesAño(item[1].valor);

                if (fecha_inicial>fecha_final){
                    alerta("En busqueda de fecha de inicio de tramite, la fecha inicial no puede ser mayor que la fecha final");
                    return false;
                }
            });
        }

        if (obj != null){
            obj.operacion = $("input[type='radio'][name='comb']:checked").val();
        }

        json = JSON.stringify(obj);
    }

    if (json !== ""){
        return json;
    }
}
function parsearFechaDiaMesAño(input) {
    //formato DD/MM/AAAA
    var parts = input.split('/');
    // new Date(year, month [, day [, hours[, minutes[, seconds[, ms]]]]])
    return new Date(parts[2], parts[1]-1, parts[0]); // Note: months are 0-based
}


function ocultarMenos(){

    if ($("body div.lista-busqueda div.item-busqueda").length > 1){
        $("body div.lista-busqueda div.item-busqueda:eq(0)  div.form-group.pull-right a:eq(0) img").css("visibility", "visible");
    }else{
        $("body div.lista-busqueda div.item-busqueda:eq(0)  div.form-group.pull-right a:eq(0) img").css("visibility", "hidden");
    }

}
$('#ayuda_operadores').popover();


// agregar clase desde el contexto del  "option" de "select" hacia el input text del formulario para hacer la sugerencia.
$.fn.agregarClaseInput = function(clase) {

    $(this).closest('.form-group').next().find('.busqueda_normal').find("input.typeahead").typeahead("destroy").removeClass (function (index, css) {
        return (css.match (/\bsugerencia-topico-\S+/g) || []).join(' ');
    }).removeClass("typeahead");

    return $(this).closest('.form-group').next().find('.busqueda_normal').find("input").addClass(clase);
};


// sugerir
function sugerirTopico(){

    //$('input[type="text"].typeahead').typeahead('destroy');
    $('input[type="text"].sugerencia-topico-numeroley:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-numeroley',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=numeroley&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");

    $('input[type="text"].sugerencia-topico-articulos:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-articulos',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=articulos',
            replace: function(url, uriEncodedQuery) {
                numeroley = $("input.sugerencia-topico-numeroley:first").val();
                if (!numeroley) return null;
                return url + '&numeroley=' + encodeURIComponent(numeroley) + '&palabra='+uriEncodedQuery
            }
        }
    }).addClass("con_sugerencia");
  /*  $('input[type="text"].sugerencia-topico-palabras_frases:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-palabras_frases',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=palabras_frases&palabra=%QUERY'
        }
    }).addClass("con_sugerencia"); */
    $('input[type="text"].sugerencia-topico-numero_boletines:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-numero_boletines',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=numero_boletines&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
    $('input[type="text"].sugerencia-topico-autores:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-autores',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=autores&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
    $('input[type="text"].sugerencia-topico-camaras:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-camaras',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=camaras&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
    $('input[type="text"].sugerencia-topico-comisiones:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-comisiones',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=comisiones&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
    $('input[type="text"].sugerencia-topico-personas_intervienes:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-personas_intervienes',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=personas_intervienes&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
    $('input[type="text"].sugerencia-topico-acuerdos:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-acuerdos',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=acuerdos&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
    $('input[type="text"].sugerencia-topico-iniciativas:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-iniciativas',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=iniciativas&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
    $('input[type="text"].sugerencia-topico-ministerio:not(.con_sugerencia)').typeahead({
        name : 'sugerencia-topico-ministerio',
        limit: 10,
        remote: {
            url : 'index.php?eID=sugerenciaBusqueda&topico=ministerio&palabra=%QUERY'
        }
    }).addClass("con_sugerencia");
}


function cargarUrlAjax(url, selector, selector_propio){
    $("#xajax-response").html('<div class="cargando"><h3>Generando resultados...</h3><img src="fileadmin/template/img/loading.gif"/></div>');
    //$("body").css("cursor", "wait");
    $(selector_propio).load(url+" "+selector , function(){
        //$("body").css("cursor", "auto");
        $('select.sel_cantidad').val(10);
        actualizarLimiteResultadoPorPaginas();
        mostrarPagina(1);
    });
}
function alerta(mensaje, titulo){
    if (typeof titulo == "undefined"){
        titulo = "Error:"
    }

    html = $('<div id="ventana-errores"><p>'+mensaje+'</p></div>');
    html.dialog(
        {
            title: titulo,
            modal: true,
            buttons: [
                {
                    text: "Cerrar Ventana", click: function () {
                        $(this).dialog("close");
                    }
                }
            ],
            width: 360
        }
    );
}

/**
 * solo ejemplo de validacion
 * @param textbox
 * @param e
 * @returns {Boolean}
 */
function invalidMsg(textbox, e) {
    console.log("input valor ("+textbox.value+")");
    console.log(e);

    if (textbox.value === "") {
        textbox.setCustomValidity("Debe ingresar un valor");
        return false;
    }
    else{
        textbox.setCustomValidity("");
        return true;
   }

}
/*
//  bcn_listaresultadobusqueda
*/
/*
CryptoJS v3.1.2
code.google.com/p/crypto-js
(c) 2009-2013 by Jeff Mott. All rights reserved.
code.google.com/p/crypto-js/wiki/License
*/
var CryptoJS=CryptoJS||function(h,r){var k={},l=k.lib={},n=function(){},f=l.Base={extend:function(a){n.prototype=this;var b=new n;a&&b.mixIn(a);b.hasOwnProperty("init")||(b.init=function(){b.$super.init.apply(this,arguments)});b.init.prototype=b;b.$super=this;return b},create:function(){var a=this.extend();a.init.apply(a,arguments);return a},init:function(){},mixIn:function(a){for(var b in a)a.hasOwnProperty(b)&&(this[b]=a[b]);a.hasOwnProperty("toString")&&(this.toString=a.toString)},clone:function(){return this.init.prototype.extend(this)}},
j=l.WordArray=f.extend({init:function(a,b){a=this.words=a||[];this.sigBytes=b!=r?b:4*a.length},toString:function(a){return(a||s).stringify(this)},concat:function(a){var b=this.words,d=a.words,c=this.sigBytes;a=a.sigBytes;this.clamp();if(c%4)for(var e=0;e<a;e++)b[c+e>>>2]|=(d[e>>>2]>>>24-8*(e%4)&255)<<24-8*((c+e)%4);else if(65535<d.length)for(e=0;e<a;e+=4)b[c+e>>>2]=d[e>>>2];else b.push.apply(b,d);this.sigBytes+=a;return this},clamp:function(){var a=this.words,b=this.sigBytes;a[b>>>2]&=4294967295<<
32-8*(b%4);a.length=h.ceil(b/4)},clone:function(){var a=f.clone.call(this);a.words=this.words.slice(0);return a},random:function(a){for(var b=[],d=0;d<a;d+=4)b.push(4294967296*h.random()|0);return new j.init(b,a)}}),m=k.enc={},s=m.Hex={stringify:function(a){var b=a.words;a=a.sigBytes;for(var d=[],c=0;c<a;c++){var e=b[c>>>2]>>>24-8*(c%4)&255;d.push((e>>>4).toString(16));d.push((e&15).toString(16))}return d.join("")},parse:function(a){for(var b=a.length,d=[],c=0;c<b;c+=2)d[c>>>3]|=parseInt(a.substr(c,
2),16)<<24-4*(c%8);return new j.init(d,b/2)}},p=m.Latin1={stringify:function(a){var b=a.words;a=a.sigBytes;for(var d=[],c=0;c<a;c++)d.push(String.fromCharCode(b[c>>>2]>>>24-8*(c%4)&255));return d.join("")},parse:function(a){for(var b=a.length,d=[],c=0;c<b;c++)d[c>>>2]|=(a.charCodeAt(c)&255)<<24-8*(c%4);return new j.init(d,b)}},t=m.Utf8={stringify:function(a){try{return decodeURIComponent(escape(p.stringify(a)))}catch(b){throw Error("Malformed UTF-8 data");}},parse:function(a){return p.parse(unescape(encodeURIComponent(a)))}},
q=l.BufferedBlockAlgorithm=f.extend({reset:function(){this._data=new j.init;this._nDataBytes=0},_append:function(a){"string"==typeof a&&(a=t.parse(a));this._data.concat(a);this._nDataBytes+=a.sigBytes},_process:function(a){var b=this._data,d=b.words,c=b.sigBytes,e=this.blockSize,f=c/(4*e),f=a?h.ceil(f):h.max((f|0)-this._minBufferSize,0);a=f*e;c=h.min(4*a,c);if(a){for(var g=0;g<a;g+=e)this._doProcessBlock(d,g);g=d.splice(0,a);b.sigBytes-=c}return new j.init(g,c)},clone:function(){var a=f.clone.call(this);
a._data=this._data.clone();return a},_minBufferSize:0});l.Hasher=q.extend({cfg:f.extend(),init:function(a){this.cfg=this.cfg.extend(a);this.reset()},reset:function(){q.reset.call(this);this._doReset()},update:function(a){this._append(a);this._process();return this},finalize:function(a){a&&this._append(a);return this._doFinalize()},blockSize:16,_createHelper:function(a){return function(b,d){return(new a.init(d)).finalize(b)}},_createHmacHelper:function(a){return function(b,d){return(new u.HMAC.init(a,
d)).finalize(b)}}});var u=k.algo={};return k}(Math);

/*
CryptoJS v3.1.2
code.google.com/p/crypto-js
(c) 2009-2013 by Jeff Mott. All rights reserved.
code.google.com/p/crypto-js/wiki/License
*/
(function(E){function h(a,f,g,j,p,h,k){a=a+(f&g|~f&j)+p+k;return(a<<h|a>>>32-h)+f}function k(a,f,g,j,p,h,k){a=a+(f&j|g&~j)+p+k;return(a<<h|a>>>32-h)+f}function l(a,f,g,j,h,k,l){a=a+(f^g^j)+h+l;return(a<<k|a>>>32-k)+f}function n(a,f,g,j,h,k,l){a=a+(g^(f|~j))+h+l;return(a<<k|a>>>32-k)+f}for(var r=CryptoJS,q=r.lib,F=q.WordArray,s=q.Hasher,q=r.algo,a=[],t=0;64>t;t++)a[t]=4294967296*E.abs(E.sin(t+1))|0;q=q.MD5=s.extend({_doReset:function(){this._hash=new F.init([1732584193,4023233417,2562383102,271733878])},
_doProcessBlock:function(m,f){for(var g=0;16>g;g++){var j=f+g,p=m[j];m[j]=(p<<8|p>>>24)&16711935|(p<<24|p>>>8)&4278255360}var g=this._hash.words,j=m[f+0],p=m[f+1],q=m[f+2],r=m[f+3],s=m[f+4],t=m[f+5],u=m[f+6],v=m[f+7],w=m[f+8],x=m[f+9],y=m[f+10],z=m[f+11],A=m[f+12],B=m[f+13],C=m[f+14],D=m[f+15],b=g[0],c=g[1],d=g[2],e=g[3],b=h(b,c,d,e,j,7,a[0]),e=h(e,b,c,d,p,12,a[1]),d=h(d,e,b,c,q,17,a[2]),c=h(c,d,e,b,r,22,a[3]),b=h(b,c,d,e,s,7,a[4]),e=h(e,b,c,d,t,12,a[5]),d=h(d,e,b,c,u,17,a[6]),c=h(c,d,e,b,v,22,a[7]),
b=h(b,c,d,e,w,7,a[8]),e=h(e,b,c,d,x,12,a[9]),d=h(d,e,b,c,y,17,a[10]),c=h(c,d,e,b,z,22,a[11]),b=h(b,c,d,e,A,7,a[12]),e=h(e,b,c,d,B,12,a[13]),d=h(d,e,b,c,C,17,a[14]),c=h(c,d,e,b,D,22,a[15]),b=k(b,c,d,e,p,5,a[16]),e=k(e,b,c,d,u,9,a[17]),d=k(d,e,b,c,z,14,a[18]),c=k(c,d,e,b,j,20,a[19]),b=k(b,c,d,e,t,5,a[20]),e=k(e,b,c,d,y,9,a[21]),d=k(d,e,b,c,D,14,a[22]),c=k(c,d,e,b,s,20,a[23]),b=k(b,c,d,e,x,5,a[24]),e=k(e,b,c,d,C,9,a[25]),d=k(d,e,b,c,r,14,a[26]),c=k(c,d,e,b,w,20,a[27]),b=k(b,c,d,e,B,5,a[28]),e=k(e,b,
c,d,q,9,a[29]),d=k(d,e,b,c,v,14,a[30]),c=k(c,d,e,b,A,20,a[31]),b=l(b,c,d,e,t,4,a[32]),e=l(e,b,c,d,w,11,a[33]),d=l(d,e,b,c,z,16,a[34]),c=l(c,d,e,b,C,23,a[35]),b=l(b,c,d,e,p,4,a[36]),e=l(e,b,c,d,s,11,a[37]),d=l(d,e,b,c,v,16,a[38]),c=l(c,d,e,b,y,23,a[39]),b=l(b,c,d,e,B,4,a[40]),e=l(e,b,c,d,j,11,a[41]),d=l(d,e,b,c,r,16,a[42]),c=l(c,d,e,b,u,23,a[43]),b=l(b,c,d,e,x,4,a[44]),e=l(e,b,c,d,A,11,a[45]),d=l(d,e,b,c,D,16,a[46]),c=l(c,d,e,b,q,23,a[47]),b=n(b,c,d,e,j,6,a[48]),e=n(e,b,c,d,v,10,a[49]),d=n(d,e,b,c,
C,15,a[50]),c=n(c,d,e,b,t,21,a[51]),b=n(b,c,d,e,A,6,a[52]),e=n(e,b,c,d,r,10,a[53]),d=n(d,e,b,c,y,15,a[54]),c=n(c,d,e,b,p,21,a[55]),b=n(b,c,d,e,w,6,a[56]),e=n(e,b,c,d,D,10,a[57]),d=n(d,e,b,c,u,15,a[58]),c=n(c,d,e,b,B,21,a[59]),b=n(b,c,d,e,s,6,a[60]),e=n(e,b,c,d,z,10,a[61]),d=n(d,e,b,c,q,15,a[62]),c=n(c,d,e,b,x,21,a[63]);g[0]=g[0]+b|0;g[1]=g[1]+c|0;g[2]=g[2]+d|0;g[3]=g[3]+e|0},_doFinalize:function(){var a=this._data,f=a.words,g=8*this._nDataBytes,j=8*a.sigBytes;f[j>>>5]|=128<<24-j%32;var h=E.floor(g/
4294967296);f[(j+64>>>9<<4)+15]=(h<<8|h>>>24)&16711935|(h<<24|h>>>8)&4278255360;f[(j+64>>>9<<4)+14]=(g<<8|g>>>24)&16711935|(g<<24|g>>>8)&4278255360;a.sigBytes=4*(f.length+1);this._process();a=this._hash;f=a.words;for(g=0;4>g;g++)j=f[g],f[g]=(j<<8|j>>>24)&16711935|(j<<24|j>>>8)&4278255360;return a},clone:function(){var a=s.clone.call(this);a._hash=this._hash.clone();return a}});r.MD5=s._createHelper(q);r.HmacMD5=s._createHmacHelper(q)})(Math);


function md5(value) {
    return CryptoJS.MD5(value).toString();
}


/*
 * Paginador
 */
function mostrarItems(limite_inferior, limite_superior){

    $("ul.paginacion:eq(0) li").each(function() {
        $(this).show();
    });

    $("ul.paginacion:eq(1) li").each(function() {
        $(this).show();
    });

    $("ul.paginacion:eq(0) li:gt("+(limite_superior-1)*2+")").each(function() {
        $(this).hide();
    });

    $("ul.paginacion:eq(0) li:lt("+(limite_inferior-1)*2+")").each(function() {
        $(this).hide();
    });

    $("ul.paginacion:eq(1) li:gt("+(limite_superior-1)*2+")").each(function() {
        $(this).hide();
    });

    $("ul.paginacion:eq(1) li:lt("+(limite_inferior-1)*2+")").each(function() {
        $(this).hide();
    });
}
function calcularItemsLi(next){
    var limit = 7; // limite izquierda y derecha
    var first = 1; // parte de 1
    var last = $("ul.paginacion:eq(0) li.link").length; // ultimo valor de paginador

    var lot = parseInt(limit/2);
    var left = next-lot;
    var right = next+lot;
    if(left < first){
        left = first;
        right = (next +(lot+(lot-next)))+1;
    }
    if(right > last){
        right = last;
        left = next - (lot+(lot-(last-next))) ;
        left = (left <= 0)?1:left;
    }

    mostrarItems(left, right);
}


function mostrarPagina(nro) {
    var indx = nro - 1; // los indices comienzan en 0
    $("ul.paginacion li.link").each(function() { // elimina todos los estilos del paginador
        $(this).removeClass("active");
    });

    $("ul.paginacion:eq(0) li.link:eq(" + indx + ")").addClass("active"); // agrega estilo al contador de paginacion superior
    $("ul.paginacion:eq(1) li.link:eq(" + indx + ")").addClass("active"); // agrega estilo al contador de paginacion inferior


    $(".pagina").css('display', 'none'); // oculta todos los resultados de búsqueda
    $('.pagina_' + nro).css('display', 'block'); // muestra sólo el correspondiente
    $.cookie("bcn_listaresultadobusqueda_numero_pagina", nro, { expires: 1 });
    //var key = md5(window.location.search.substring(1));
    var new_url = window.location.search.substring(1)+'#pagina-'+$('.link.active :eq(0)').html();
    var key = md5(new_url);

    var value = parseInt(nro);
    $.cookie(key, value, { expires: 7, path: '/' });

    // agregar etiqueta en span .label-numeros
    x =  (nro - 1)*$('.pagina_1').length + 1;
    y = $('.pagina_' + nro).length + (nro - 1)*$('.pagina_1').length;

    $(".label-numeros").html(x+" - "+y+" de ");
    calcularItemsLi(nro);
    $("ul.paginacion").show();
    $('.pagina_'+$('.link.active :eq(0)').html()+' a[class="enlaces"]').each(
        function(data,value){
            url = value.href;
            array_url = url.split("&pagina");
            url = array_url[0]+'&pagina-'+$('.link.active :eq(0)').html();
            value.href = url;
        }
    )
}

function paginaAnterior(){
    var current = parseInt($.cookie("bcn_listaresultadobusqueda_numero_pagina"));

    if (1 < current){
        mostrarPagina(current -1);
    }
}



function paginaSiguiente(){
    var current = parseInt($.cookie("bcn_listaresultadobusqueda_numero_pagina"));
    var last = $("ul.paginacion:eq(0) li.link").length;

    if (current < last){
        mostrarPagina(current + 1);
    }
}

function actualizarLimiteResultadoPorPaginas(){
    // al cambiar los select se actualiza el valor en el campo hidden del formulario, tambien se copian los valores entre si

    $("select.sel_cantidad").change(function() {
        $( "select.sel_cantidad").val($(this).val()); // actualiza ambos select
        actualizarResultadosPorPaginas();
    });

}

function actualizarResultadosPorPaginas(){
    $("div.row.pagina").removeClass (function (index, css) {
        return (css.match (/\bpagina_\S+/g) || []).join(' ');
    });
    var cnt_resultados  = $("div.row.pagina").length;
    var cnt_resultados_por_pagina  = parseInt( $('select.sel_cantidad:first').val() );
    var cnt_paginas = parseInt(cnt_resultados/cnt_resultados_por_pagina);
    cnt_paginas = (cnt_resultados%cnt_resultados_por_pagina!== 0)?++cnt_paginas:cnt_paginas; // si el resto es distinto de cero, incrementar en una unidad cnt_paginas.
    $("#bcn_listaresultadobusqueda  table td.col-sm-5  div  a.link-ultimo").prop("href", "javascript:mostrarPagina("+cnt_paginas+")");

    var i = 0;
    var j = 1;
    $("div.row.pagina").each(function( index ) {

        if (cnt_resultados_por_pagina === i){
            i = 0;
            j++;
        }
        ++i;

        $( this ).addClass("pagina_"+j);
    });

    $("div.row.pagina.pagina_1").show();
    $("div.row.pagina:not(.pagina_1)").hide();

    //agregar paginacion
    $("ul.paginacion").hide();

    $("ul.paginacion").empty();
    var tmp;
    for (var k =  0; k < cnt_paginas; k++) {
        tmp = k +1;
        $("ul.paginacion").append( '<li class="link"><a href="javascript:mostrarPagina('+tmp+');">'+tmp+'</a></li>' );
        $("ul.paginacion").append( '<li><span> - </span></li>' );
    };

    $("ul.paginacion:eq(0) li:last")


    mostrarPagina(1);
    $("ul.paginacion").show();
    $("table.expand a.link-primer").prop("href", $("ul.paginacion:eq(0) li:first a").prop("href"));
    $("table.expand a.link-ultimo").prop("href", $("ul.paginacion:eq(0) li:last a").prop("href"));
    $("ul.paginacion").show();
    sMarcado = $(".sel_cantidad").val();
    op = ($(".sel_cantidad option").length/2)-1;
    sFin = $(".sel_cantidad option:eq("+op+")").val();
    opag = ($('.paginacion li').length/2)-1;
    pag = $('.paginacion li a:eq('+opag+')').html();
    if(sMarcado == sFin && pag == 1){
        $('.paginacion').css('visibility','hidden');
        $('.text-right').css('visibility','hidden');
    }else{
        $('.paginacion').css('visibility','');
        $('.text-right').css('visibility','');
    }
}


setInterval(
    function(){
        if($('.popover-derogada').length>0 && $('body:hover').length == 1){
            $('.popover-derogada').popover();
        }
    }, 200);
function herrPersonalizarDossier(url){window.location.href = url;}