var x,w;
var y,h;
var flag = 0;

var pic_scr;
function init_pic()
{
    pic_src = window.document.getElementById('select_pic').src;
}

//detect brouser
var BrowserDetect = {
    init: function () {
        this.browser = this.searchString(this.dataBrowser) || "An unknown browser";
        this.version = this.searchVersion(navigator.userAgent)
            || this.searchVersion(navigator.appVersion)
            || "an unknown version";
        this.OS = this.searchString(this.dataOS) || "an unknown OS";
    },
    searchString: function (data) {
        for (var i=0;i<data.length;i++) {
            var dataString = data[i].string;
            var dataProp = data[i].prop;
            this.versionSearchString = data[i].versionSearch || data[i].identity;
            if (dataString) {
                if (dataString.indexOf(data[i].subString) != -1)
                    return data[i].identity;
            }
            else if (dataProp)
                return data[i].identity;
        }
    },
    searchVersion: function (dataString) {
        var index = dataString.indexOf(this.versionSearchString);
        if (index == -1) return;
        return parseFloat(dataString.substring(index+this.versionSearchString.length+1));
    },
    dataBrowser: [
        {
            string: navigator.vendor,
            subString: "Apple",
            identity: "Safari"
        },
        {
            prop: window.opera,
            identity: "Opera"
        },
        {
            string: navigator.vendor,
            subString: "iCab",
            identity: "iCab"
        },
        {
            string: navigator.vendor,
            subString: "KDE",
            identity: "Konqueror"
        },
        {
            string: navigator.userAgent,
            subString: "Firefox",
            identity: "Firefox"
        },
        {   // for newer Netscapes (6+)
            string: navigator.userAgent,
            subString: "Netscape",
            identity: "Netscape"
        },
        {
            string: navigator.userAgent,
            subString: "MSIE",
            identity: "Explorer",
            versionSearch: "MSIE"
        },
        {
            string: navigator.userAgent,
            subString: "Gecko",
            identity: "Mozilla",
            versionSearch: "rv"
        },
        {   // for older Netscapes (4-)
            string: navigator.userAgent,
            subString: "Mozilla",
            identity: "Netscape",
            versionSearch: "Mozilla"
        }
    ],
    dataOS : [
        {
            string: navigator.platform,
            subString: "Win",
            identity: "Windows"
        },
        {
            string: navigator.platform,
            subString: "Mac",
            identity: "Mac"
        },
        {
            string: navigator.platform,
            subString: "Linux",
            identity: "Linux"
        }
    ]

};
BrowserDetect.init();
var crop1;
function img_load()
{
    var o_loading = window.document.getElementById('loading');
    o_loading.style.display = 'none';
    coords_zero();
//    if(crop) crop.setParams();
}

function coords_zero()
{
    var coord_x = window.document.getElementById('coord_x');
    var coord_y = window.document.getElementById('coord_y');
    var width = window.document.getElementById('width');
    var height = window.document.getElementById('height');
    var layer = window.document.getElementById('sel');
    
    x = y = w = h = 0;
    coord_x.value = coord_y.value = width.value = height.value = 0;
    layer.style.display = 'none';
}

function getrandom() 
{ 
        var min_random = 0;
        var max_random = 1000000;
        
        max_random++;
        
        var range = max_random - min_random;
        var n=Math.floor(Math.random()*range) + min_random;
        
        return n;
}

function crop_image()
{
    
    var o_pic = window.document.getElementById('select_pic');
    var o_loading = window.document.getElementById('loading');
    var coord_x = window.document.getElementById('coord_x');
    var coord_y = window.document.getElementById('coord_y');
    var width = window.document.getElementById('width');
    var height = window.document.getElementById('height');

    if (o_pic && w>0 && h>0 && crop_started) 
    { 
    	crop_selection.cancelSelection();               
        var o_req = new Subsys_JsHttpRequest_Js();
        o_req.caching = false;
        o_req.onreadystatechange = function() {
        
            if (o_req.readyState == 4) {                                
                o_pic.src = pic_src + '?' + getrandom();                                               
 
            }
        }
        
        var o_data = {};
        o_data.action = 'im_crop';
        o_data.coord_x = x;
        o_data.coord_y = y;
        o_data.width = w;
        o_data.height = h;
        
        o_req.open('GET', '/index.php?rm=common_resize', true);
        o_req.send(o_data);
        o_loading.style.display = 'block';

	picresize.edit.updateCropDetails();
	jQuery('#cropbutton').removeClass('animated bounce infinite');
    }
    else{
	crop_selection.setSelection(50, 50, 150, 150, true);
	crop_selection.setOptions({ show: true });
	crop_selection.update();
    }
}

function rotate_image(orientation)
{

    var o_pic = window.document.getElementById('select_pic');
    var o_loading = window.document.getElementById('loading');

    if (o_pic)
    {
        var o_req = new Subsys_JsHttpRequest_Js();
        o_req.caching = false;
        o_req.onreadystatechange = function() {

            if (o_req.readyState == 4) {
                o_pic.src = pic_src + '?' + getrandom();

            }
        }

        var o_data = {};
        o_data.action = 'im_rotate';
        o_data.orientation = orientation;

	//console.log(o_data);
        o_req.open('GET', '/index.php?rm=common_resize', true);
        o_req.send(o_data);
        o_loading.style.display = 'block';

	picresize.edit.updateRotateDetails();
    }
}

function flip_image(orientation)
{

    var o_pic = window.document.getElementById('select_pic');
    var o_loading = window.document.getElementById('loading');

    if (o_pic)
    {
        var o_req = new Subsys_JsHttpRequest_Js();
        o_req.caching = false;
        o_req.onreadystatechange = function() {

            if (o_req.readyState == 4) {
                o_pic.src = pic_src + '?' + getrandom();

            }
        }

        var o_data = {};
        o_data.action = 'im_flip';
        o_data.orientation = orientation;

        //console.log(o_data);
        o_req.open('GET', '/index.php?rm=common_resize', true);
        o_req.send(o_data);
        o_loading.style.display = 'block';
    }
}


function restore_image()
{
    var answer = confirm("Are you sure you want to reset to your original picture?");
    if(answer){
    	var o_loading = window.document.getElementById('loading');
    
    	var o_req = new Subsys_JsHttpRequest_Js();
    	o_req.caching = false;
    	o_req.onreadystatechange = function() {
        	if (o_req.readyState == 4) {           
            
            		var o_pic = window.document.getElementById('select_pic');
            		o_pic.src = pic_src + '?' + getrandom();
            	
        	}
    	}
    	var o_data = {};
    	o_data.action = 'im_restore';
    
    	o_req.open('GET', '/index.php?rm=common_resize', true);
    	o_req.send(o_data);
    	o_loading.style.display = 'block';

	resetDetails();
    }

}

function onpicclick(e)
{
    var coord_x = window.document.getElementById('coord_x');
    var coord_y = window.document.getElementById('coord_y');
    var width = window.document.getElementById('width');
    var height = window.document.getElementById('height');
    if(flag == 0)
    {
        var layer = window.document.getElementById('sel');
        if(layer.style.display == 'none')
        {
            var oPosition = get_event_position1(e);
            var pic = window.document.getElementById('select_pic');
            var pic_pos = get_object_position(pic);
            if(pic_pos)
            {
                if (BrowserDetect.browser == "Explorer")
                {
                    x = (oPosition.x-pic_pos.x-1);
                    y = (oPosition.y-pic_pos.y-2);
                }
                else if(BrowserDetect.browser == "Safari")
                {
                    x = (oPosition.x-pic_pos.x-10);
                    y = (oPosition.y-pic_pos.y-10);
                }
                else
                {
                    x = (oPosition.x-pic_pos.x);
                    y = (oPosition.y-pic_pos.y);
                }
                
                w = 0; 
                h = 0;
                layer.style.top = y + 'px';
                layer.style.left = x + 'px';
                layer.style.width = w + 'px';
                layer.style.height = h + 'px';
                layer.style.display = 'block';
            }
            flag=1;
            window.document.onmousemove = move;
            var layer = window.document.getElementById('sel');
            layer.onclick = onpicclick;
        }
        else
        {
            coords_zero();
        }
    }
    else
    {
        
        coord_x.value = x;
        coord_y.value = y;
        width.value = w;
        height.value = h;
        
        window.document.onmousemove = '';
        flag = 0;
    }
    return false;
}

function get_event_position1(e) 
{
    var oPosition = {x:0, y:0};
    if (!e) var e = window.event;
    if (e.pageX || e.pageY)     
    {
        oPosition.x = e.pageX;
        oPosition.y = e.pageY;
    }
    else (e.clientX || e.clientY)   
    {
        oPosition.x = e.clientX + document.body.scrollLeft + document.documentElement.scrollLeft;
        oPosition.y = e.clientY + document.body.scrollTop + document.documentElement.scrollTop;
    }
    return oPosition;
}

function move(e)
{
    var oPosition = get_event_position1(e);
    var pic = window.document.getElementById('select_pic');
    var pic_pos = get_object_position(pic);
    if(pic_pos)
    {
        
        var layer = window.document.getElementById('sel');
        if(BrowserDetect.browser == "Safari")
        {
            w = (oPosition.x-pic_pos.x-x-9);
            h = (oPosition.y-pic_pos.y-y-9);
        }
        else
        {
            w = (oPosition.x-pic_pos.x-x+1);
            h = (oPosition.y-pic_pos.y-y+1);
        }
        if(((x+w) <= pic.width) && (w>0)) layer.style.width = w + 'px';
        if(((y+h) <= pic.height) && (h>0)) layer.style.height = h + 'px';
        
    }
    
    //pic.onmouseover = get_event_position;
    //pic.onmouseout = test;
    //pic.onclick = test;
    return false;
}

function get_object_position(obj)
{
    var oPosition = {x:0, y:0};
    if (obj == null)
    return oPosition;

    if (obj.offsetParent)
    {
       while (obj.offsetParent)
      {
                                oPosition.x += obj.offsetLeft;
                                oPosition.y += obj.offsetTop;
                                obj = obj.offsetParent;
                        }
                }
        else if (obj.x)
    {
                oPosition.x += obj.x;
        oPosition.y += obj.y;
    }

    return oPosition;
}
