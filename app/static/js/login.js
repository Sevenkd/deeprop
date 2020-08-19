$(function(){
    $(".btn").click(function(){
        var username = $("#inputUsr").val();
        var password = $("#inputPassword").val();
        $.ajax({
                    url: 'http://127.0.0.1:5000/login_verify', // 地址+路由后缀
                    type: "post",
                    data:{
                        "username": username,
                        "password": password
                    },
                    dataType: "json",
                    async: false, // 表示同步或异步, 根据实际情况设置
                    success: function (data) { // 和后台交互成功后执行的函数
                        if (data.res == 'success') {
                            alert("登陆成功！");
                            window.location.href = ".../templates/index.html";
                            // $(location).prop('href', '../index/index.html');
                            debugger;
                            console.log(data);
                        }
                        else {
                            alert("账号或密码错误");
                        }
                    },
                    error: function () { // 因网络错误或服务器后台错误(404, 500等情况)等没有成功完成数据交互执行的函数
                        alert("error");
                    }
                });
    });
})