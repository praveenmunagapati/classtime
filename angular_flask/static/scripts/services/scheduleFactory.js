/**
 * Created by Andrew on 14-11-09.
 */
coreModule.factory('scheduleFactory', function ($window, $http, $q) {
    var factory = {};

    factory.getSchedules = function (addedCourses) {
        // It gets here...hone this out to make the api call work

        //$window.alert(addedCourses[0]);
        var requestParams = {};
        requestParams["institution"] = "ualberta";
        requestParams["term"] = "1490";
        requestParams["courses"] = addedCourses;

        return( $http({method: 'GET', url: '/api/generate-schedules?q=' + angular.toJson(requestParams) }) );

    };

    return factory;

});