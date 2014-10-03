function toggleMessageAndMarkRead(id){
	msg = $('#messageContent'+id);
	msg.toggle();
	if(msg.attr('data-read')!='1'){
		msg.attr('data-read', 1);
		$.get('/messages/read/'+id);
		$("#messageCount").html($("#messageCount").html()-1);
	}
	$('#messageTitle'+id).css("font-weight", "normal");
}

function insertNewMessages(data){
	if(data == null){
		return;
	}
	if(data.unreadMessages > 0){
		$("#messageCount").html(data.unreadMessages);
		$("#messageCount").parent().show();
	}else
		$("#messageCount").parent().hide();
}

function getNewMessages(){
	$.ajax({url: "/messages/digest",
		 dataType: "json",
		 success: insertNewMessages});
}



function removeMessage(elem){
	$(elem).parent().fadeOut({complete:function(){
						$(this).remove();
						if($(".message").size() == 0)
							$("#messageViewBlocker").remove();
						}
					});
}

function removeFirstMessage(){
	removeMessage($(".message").first().children().first());
}

function checkUserInput(){
	form = $(this);
	result = true;
	form.find("input,password,textarea").each(function(k, e){
		$(e).removeClass("wrongInput");
		if($(e).attr("data-dataType") == "int"){
			if(!$(e).val().match(/^[\d]+$/)){
				result = false;
				$(e).addClass("wrongInput");
			}
		}else if($(e).attr("data-dataType") == "stringNotEmpty"){
			if($(e).val().match(/^[\s]*$/)){
				result = false;
				$(e).addClass("wrongInput");
			}
		}else if($(e).attr("data-dataType") == "customRegex"){
			regex = new RegExp($(e).attr("data-regExp"));
			if(!$(e).val().match(regex)){
				result = false;
				$(e).addClass("wrongInput");
			}
		}
	});
	
	if(!result){
		alert("Du hast in einem Feld eine nicht erlaubte Zeichenkette eingegeben!");
	}
	
	return result;
}
			
			
function init(){
	//getNewMessages();
	//window.setInterval("getNewMessages();", 5*60*1000);
	
	$("form").each(function(k, e){
		$(e).submit(checkUserInput);
	});
	
	if($(".message").size() != 0){
		$(".message").first().children("button").first().focus();
	}
}

$(document).ready(init);
