$(function(){
    $(".btn").click(function(){
        var username = $("#inputUsr").val();
        var password = $("#inputPassword").val();
        $.ajax({
                    url: '/login', // 地址+路由后缀
                    type: "post",
                    data:{
                        "username": username,
                        "password": password
                    },
                    dataType: "json",
                    async: false, // 表示同步或异步, 根据实际情况设置
                    success: function (data) { // 和后台交互成功后执行的函数
                        if (data.res == 'success') {
                            console.log(data)
                            let nextView = data.next;
                            if (!nextView) {
                                window.location.href = "/";
                                return;
                            }
                            window.location.href = nextView;
                        }
                        else {
                            // TODO: flush 错误信息
                            alert(data.desc);
                        }
                    },
                    error: function () { // 因网络错误或服务器后台错误(404, 500等情况)等没有成功完成数据交互执行的函数
                        alert("网络错误, 请稍后再试!");
                    }
                });
    });
})