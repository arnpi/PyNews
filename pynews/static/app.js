var app = angular.module('myTestApp', ['angularMoment']).constant('angularMomentConfig', {
    preprocess: 'unix', // optional
    timezone: 'Europe/Paris' // optional
}).filter('moment', function() {
    return function(dateString, format) {
        return moment(dateString).format(format);
    };
});;;;

app.controller('loginController', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http, $interval) {

    $rootScope.showDiv = function(type_div) {
        $rootScope.showMeteo = false;
        $rootScope.showNote = false;
        $rootScope.showMail = false;
        $rootScope.showTwitter = false;
        $rootScope.showNews = false;
        $rootScope.showAdmin = false;
        if (type_div == 'meteo') {
            $rootScope.showMeteo = true;
        }
        else if (type_div == 'note') {
            $rootScope.showNote = true;
        }
        else if (type_div == 'mail') {
            $rootScope.showMail = true;
        }
        else if (type_div == 'twitter') {
            $rootScope.showTwitter = true;
        }
        else if (type_div == 'news') {
            $rootScope.showNews = true;
        }
        else if (type_div == 'admin') {
            $rootScope.showAdmin = true;
        }
    }

    $rootScope.showNews = true;

    $scope.checkLogin = function() {
        $http.get('/status_login').success(function(data) {
            console.log(data);
            $scope.status_login = data.status_login;
            $scope.status = data.status;
        });
    }
    $scope.startAll = function() {

    }

    $scope.loginSend = function() {
        // $http.get('/login/' + $scope.login + '/' + $scope.password).success(function(data) {
        $http.get('/login/admin/admin').success(function(data) {
            console.log(data);

            $scope.checkLogin();
            if($scope.status != data.status) {
                window.location.href = "/";
            }
        });
    }

    $scope.logoutSend = function() {
        $http.get('/logout').success(function(data) {
            $scope.checkLogin();
            if($scope.status != data.status) {
                window.location.href = "/";
            }
        });
    }

    $scope.checkLogin();
    setInterval(function(){
        $scope.$apply(function() {
            console.log('check login');
            $scope.checkLogin();
        });
    }, 120000);

}]);

app.controller('adminController', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http, $interval) {

    $scope.updateTwitterKey = function(twitter_api_key, twitter_api_secret) {

        $http.get('/register_api_twitter/' + twitter_api_key + "/" + twitter_api_secret).success(function(data) {
            console.log(data);
            console.log("updated");
        });
    }

}]);

app.controller('mailsController', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http, $interval) {

    $scope.getMails = function() {

        $http.get('/mail').success(function(data) {
            $scope.accounts = data.mails;
            console.log(data);
            if (data.mails[0] == "Error while connecting to imap server") {
                console.log("network error, trying local storage");
                // $scope.accounts = JSON.parse(sessionStorage.getItem("mails"));
            }
            else {
                console.log("mail fail");
                // sessionStorage.setItem("mails",JSON.stringify(data.mails));
            }
        });
    }

    //if ($rootScope.showMail == true) {
        $scope.getMails();
    //}
    setInterval(function(){
        $scope.$apply(function() {
        if ($rootScope.showMail == true) {
                console.log('mails refresh');
                $scope.getMails();
            }
        });
    }, 120000);

}]);

app.controller('meteoController', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http, $interval) {
    
    delete $http.defaults.headers.common['X-Requested-With'];

    $scope.getMeteo = function() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position){
                var latitude = position.coords.latitude;
                var longitude = position.coords.longitude;
                var altitude = position.coords.altitude;
                $http.defaults.useXDomain = true;
                $.support.cors = true;
                $http.get("http://api.openweathermap.org/data/2.5/weather?lat=" +latitude + "&lon=" +longitude+ "&units=metric&lang=fr").success(function(data) {
                    $scope.weather = data;
                });
            }, function(){
                console.log('localistation nok');
            });
        }
        else {
            console.log("Votre navigateur ne prend pas en compte la géolocalisation HTML5");
        }
        $scope.imageSource = "http://www.meteociel.fr/prevision/prev0.png";
        $scope.imageSourceGif = "http://neige.meteociel.fr/satellite/anim_ir_color.gif";

    }

    $scope.getMeteo();

    setInterval(function(){
        $scope.$apply(function() {
            if($rootScope.showMeteo == true) {
                console.log('meteo refresh');
                $scope.getMeteo();
	    }
        });
    }, 120000);
}]).config(function($httpProvider){
    delete $httpProvider.defaults.headers.common['X-Requested-With'];
});

app.controller('notesController', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http) {

    $scope.getNotesList = function() {
        $http.get('/notes/list').success(function(data) {
            $scope.notes_list = data.notes;
            $scope.getNote($scope.notes_list[0].id);
        });
    }

    $scope.getNote = function(id) {
        $http.get('/note/' + id).success(function(data) {
            $scope.note = data.note;
            $scope.id = data.id;
            $scope.selectedNote = id;
            console.log($scope.selectedNote);
        });
    }

    $scope.setNote = function(id) {
        var encodedData = window.btoa($scope.note);
        $http.get('/note/update/' + id +'/' + encodedData).success(function(data) {
            $scope.note = data.note;
            $scope.id = data.id;
        });
    }

    $scope.deleteNote = function(id) {
        $http.get('/notes/delete/' + id).success(function(data) {
            $scope.note = data.note;
            $scope.id = data.id;
            $scope.getNotesList();
        });
    }

    $scope.addNote = function(title) {
        var encodedData = window.btoa(title + " content ...");
        var encodedData2 = window.btoa(title);
        $http.get('/notes/add/' + encodedData2 + "/" + encodedData).success(function(data) {
            $scope.note = data.note;
            $scope.id = data.id;
            $scope.getNotesList();
        });
    }

    $scope.getNotesList();

}]);

app.controller('twitterController', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http, $interval) {

    moment.locale('fr');
    $scope.scale = 24;
    $scope.hidden = 0;
    $scope.showStart = 0;
    $scope.showEnd = $scope.scale;

    $scope.loginTwitter = function() {
        $http.get('/auth_twitter').success(function(data) {
            console.log(data.twitter);
            window.open(data.twitter.url);
            $scope.loginTwitter = data.twitter;
        });
    }

    $scope.endLoginTwitter = function() {
        $http.get('/end_auth_twitter/' + $scope.loginTwitter.oauth_token + "/" + $scope.loginTwitter.token_secret + "/" + $scope.endTwitter).success(function(data) {
            console.log(data.twitter);
            $scope.checkTwitter();
        });
    }

    $scope.checkTwitter = function() {
        // $http.get('/static/twitter.json').success(function(data) {
        $http.get('/twitter').success(function(data) {
            console.log($scope);
            console.log(data);
            if (data.feed == "no twitter") {
                $scope.twitterError = 1;
                console.log('error !!!!!');
            }
            else {
                $scope.twitterError = 0;
                $scope.twitter = data.twitter;
                $scope.count = data.twitter.length;
            }
        });
    }

    $scope.showTen = function(variable) {
        $scope.hidden = 0;
        $scope.showStart = variable;
        $scope.showEnd = variable+$scope.scale;
    }
    $scope.showAll = function() {
        $scope.hidden = 0;
        $scope.showStart =  0;
        $scope.showEnd = $scope.count;
    }

    //if($rootScope.showTwitter) {
         $scope.checkTwitter();
         $scope.select = 1;
    //}
    setInterval(function(){
        $scope.$apply(function() {
            if($rootScope.showTwitter) {
                console.log('twitter refresh');
                $scope.checkTwitter();
            }
        });
    }, 120000);

}]);

app.controller('newsController', ['$scope', '$rootScope', '$http', function($scope, $rootScope, $http, $interval) {
$scope.localStorageFeed = {};
    $scope.getCategories = function() {
        $scope.categories = [];
        $http.get('/categories/list').success(function(data) {
            $scope.model = {};
            $scope.categories = data.categories;
            $scope.getCategoryFeeds($scope.categories[0].id);
            $scope.selectedCategoryId = $scope.categories[0].id;
            
            $scope.selectedCategoryName = $scope.categories[0].name;
            return data;
        });
    }
    $scope.getCategories();

    $scope.getCategoryFeeds = function(id, name) {
        $scope.selectedCategory = id;
        $scope.selectedCategoryId = id;
        $scope.selectedCategoryName = name;
        $http.get('/rsses_by_category/' + id).success(function(data) {
            // console.log(data.rsses);
            $scope.feedsList = data.rsses;
            $scope.getFeedList(data.rsses[0]);
            $scope.selectedUrl = data.rsses[0];
            return data.rsses;
        });
    }

    $scope.getFeedList = function(sender) {
        $scope.newsIsLoading = true;
        $scope.newsError = false;
        $scope.newsNoErrorNoLoading = false;
        $http.get('/feed/' + sender.id).success(function(data) {
            console.log(data.title)
            // console.log(data.feed);
            if (data.feed == "error") {
                console.log("no internet");
                // $scope.contentList = JSON.parse(localStorage.getItem("feed_" + sender.id));
                $scope.errorMsg = sender.title;
                console.log(sender.title);
                $scope.contentList = sender;
                // $scope.contentList = JSON.parse($scope.contentList);
                // console.log($scope.contentList.feed.content[0]);
                // console.log($scope.contentList);
                // console.log(sessionStorage);
                // console.log(sessionStorage.getItem("feed_" + sender.id));
                // var feed = localStorage.getItem("feed_" + sender.id);
                // console.log(JSON.parse(feed));
                // console.log(feed.getItem("feed_" + sender.id), JSON.parse(feed));
                // console.log("error while fetching feeds, trying local storage");
                // console.log($scope.contentList);


                
                // $scope.showContent($scope.contentList.content[0]);
                // $scope.localStorageFeed[sender.id] = true;
                $scope.selectedUrl = sender;
                $scope.newsNoErrorNoLoading = true;
                $scope.newsIsLoading = false;
                $scope.newsError = true;
                return $scope.contentList;       
            }
            else {
                // $scope.localStorageFeed[sender.id] = false;
                $scope.contentList = data.feed;
                console.log(data.feed);


                // tmp_data = JSON.stringify(data.feed);
                // sessionStorage.getItem("mails");
                // localStorage.setItem("feed_" + sender.id, tmp_data);
                // var tmp_feed= localStorage.getItem("feed_" + sender.id);

                // console.log($scope.contentList);
                // console.log(JSON.parse(localStorage.getItem("feed_" + sender.id)));
                // console.log(tmp_feed);
                // console.log(tmp_feed, JSON.parse(tmp_feed));
                // console.log(tmp_feed);
                // $scope.localStorageFeed[sender.id] = true;
                $scope.newsNoErrorNoLoading = true;
                $scope.showContent(data.feed.content[0]);
                $scope.selectedUrl = sender;
                $scope.newsIsLoading = false;
                return $scope.contentList;
            }
            //
        });
        // var tmp_feed = localStorage;
        // console.log(JSON.parse(tmp_feed));
    }

    $scope.showContent = function(content) {
        $scope.newsTitle = content.head;
        $scope.newsContent = content.feed;
        $scope.newsDate = content.date;
        $scope.newsLink = content.link;
    }

    $scope.getNewsListByCategory = function(id) {
        $http.get('/rsses_by_category/' + id).success(function(data) {
            return data.rsses;
        });
    }

    $scope.renameCategory = function(id, name) {
        $http.get('/category/update/' + id + "/" + name).success(function(data) {
            $scope.getCategories();
        });
    }

    $scope.deleteCategory = function(id) {
        $http.get('/categories/delete/' + id).success(function(data) {
            $scope.getCategories();
        });
    }

    $scope.updateRssCategory = function(new_category, id) {
        $http.get('/rss/update/category/' + new_category +'/' + id).success(function(data) {
            $scope.getCategories();
        });
    }

    $scope.newCategory = function() {
        $http.get('/categories/add/' + $scope.newCategoryName).success(function(data) {
            $scope.getCategories();
        });
    }

    $scope.newFeed = function() {
        var title = $scope.newRssTitle;
        if (typeof($scope.newRssTitle) == "undefined" || $scope.newRssTitle == "") {
            title = "1";
        }
        $http.get('/rsses/add/' + window.btoa(title) + "/" + window.btoa($scope.newRssUrl) + "/" + $scope.newRssUrlCat).success(function(data) {
            $scope.getCategories();
        });
    }
    $scope.deleteFeed = function(id) {
        $http.get('/rsses/delete/' + id).success(function(data) {
            $scope.getCategories();
        });
    }
    $scope.updateRssUrl = function(id, url) {
        // $http.get('/rsses/delete/' + id).success(function(data) {
        //     $scope.getCategories();
        // });
        var encodedUrl = window.btoa(url);
        console.log(id, encodedUrl);
        $http.get("/rss/update/url/" + id + "/" + encodedUrl).success(function(data) {
            $scope.getCategories();
            $scope.updateUrl = "";
        });
    }

    $scope.viewLater = function(obj) {
        var tmp_storage = JSON.parse(localStorage);
        console.log(typeof(tmp_storage));
        console.log(localStorage.view_later);
        if (typeof(localStorage.view_later == "")) {
            // localStorage.view_later = [];
            localStorage.setItem("view_later", []);
            console.log("if");
        }
        else {
            console.log("else");
        }
        // console.log("viewlater");
        // tmp_view_later = JSON.stringify(obj);
        // // console.log(tmp_view_later)
        // // sessionStorage.getItem("mails");
        // localStorage.view_later.setItem(tmp_view_later.link, tmp_view_later);
        // console.log(localStorage);
    }

    // $scope.getAllCache = function() {
    //     var tmp_localstorage = [];
    //     $http.get('/categories/list').success(function(data) {

    //         for (var i = data.categories.length - 1; i >= 0; i--) {
    //             $http.get('/rsses_by_category/' + data.categories[i].id).success(function(data) {

    //                 for (var i = data.rsses.length - 1; i >= 0; i--) {
    //                     $http.get('/feed/' + data.rsses[i].id).success(function(data) {

    //                         console.log(data.feed);
    //                     });
    //                 };
    //             });
    //         };
    //     });
    // }
    // tmp_data = JSON.stringify(data.feed);
    // // sessionStorage.getItem("mails");
    // localStorage.setItem("feed_" + sender.id, tmp_data);
    // $scope.contentList = JSON.parse(localStorage.getItem("feed_" + sender.id));


}]);



