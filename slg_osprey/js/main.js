//define user event color
var user_event_color_common = '#4472C4';
var user_event_color_highlight = '#00B0F0';

// define fps color
var fps_bar_color_1 = '#2A4981';
var fps_bar_color_2 = '#2F528F';
var fps_bar_color_3 = '#34599C';
var fps_bar_color_4 = '#3960A7';
var fps_bar_color_5 = '#3D67B1';
var fps_bar_color_6 = '#406DBB';
var fps_bar_color_7 = '#4472C4';
var fps_bar_color_8 = '#6D89CB';
var fps_bar_color_9 = '#889CD2';
var fps_bar_color_10 = '#9EADD8';
var fps_bar_color_11 = '#B0BCDE';
var fps_bar_color_12 = '#C0C9E4';
var fps_bar_color_13 = '#CFD5EA';

// define memory color
var memory_bar_color_1 = '#48722C';
var memory_bar_color_2 = '#507E32';
var memory_bar_color_3 = '#588937';
var memory_bar_color_4 = '#5F933B';
var memory_bar_color_5 = '#659C3F';
var memory_bar_color_6 = '#6BA543';
var memory_bar_color_7 = '#70AD47';
var memory_bar_color_8 = '#88B76E';
var memory_bar_color_9 = '#9BC189';
var memory_bar_color_10 = '#ACCA9E';
var memory_bar_color_11 = '#BBD3B1';
var memory_bar_color_12 = '#C9D8C1';
var memory_bar_color_13 = '#D5E3CF';

function setEventSettings(title, jsonfeed, highlight_index_from, highlight_index_to) {
    var settings = {
        title: title,
        description: '',
        enableAnimations: true,
        showLegend: false,
        padding: { left: 40, top: 10, right: 40, bottom: 40 },
        titlePadding: { left: 90, top: 15, right: 0, bottom: 20 },
        source: jsonfeed,
        xAxis:
            {
                dataField: '埋点',
                showTickMarks: true,
                tickMarksInterval: 1,
                tickMarksColor: '#888888',
                unitInterval: 1,
                showGridLines: false,
                gridLinesInterval: 1,
                gridLinesColor: '#888888',
                axisSize: 'auto',
                flip: false,
                //textRotationAngle: 90,
                labels : {
                    angle: 90,
                    horizontalAlignment: 'left',
                    verticalAlignment: 'center',
                    rotationPoint: 'left',
                    offset: { y: -115 }
                }
            },
        //colorScheme: 'scheme01',
        seriesGroups:
            [
                {
                    type: 'column',
                    columnsGapPercent: 15,
                    //click: barChartSeverityHandler,
                    //orientation: 'horizontal',
                    valueAxis:
                    {
                        unitInterval: 20,
                        minValue: 0,
                        displayValueAxis: true,
                        description: '',
                        tickMarksColor: '#888888',
                        showTickMarks: false
                        //flip: true
                        
                    },
                    series: [
                                { dataField: '百分比', displayText: '百分比', showLabels: true, 
                                  colorFunction: function (value, itemIndex, serie, group) {
                                    if(itemIndex > highlight_index_from && itemIndex < highlight_index_to) {
                                        return user_event_color_highlight;
                                    } else {
                                        return user_event_color_common;
                                    }
                                 } 
                                }
                    ]
                }
            ]
    };
    
    return settings;
}

function drawBarChartEvent() {
	
    var bar_jsonfeed = new Array();
    var bar_jsonfeed_iglk = new Array();
    var $total = 0;
    
    // get the dataAdapter for source in settings
    $.ajax({
        type: 'GET',
        url: 'data/user_event.json',
        dataType: 'json',
        async: false,
        cache: false,
        success: function(responseJSON){
            
            $.each(responseJSON,function(i,item){
                
                
                
                if(i==0){
                    $total = parseInt(item.value);
                }
                
                if(i==1){
                    $total_iglk = parseInt(item.value);
                }

                bar_jsonfeed.push(
                    {
                        '埋点' : item.event,
                        '百分比' : (parseFloat(parseInt(item.value)/$total)*100).toFixed(2)
                    }
                );
                
                if(i>0){
                    bar_jsonfeed_iglk.push(
                        {
                            '埋点' : item.event,
                            '百分比' : (parseFloat(parseInt(item.value)/$total_iglk)*100).toFixed(2)
                        }
                    );
                }
            })
        },
        error: function (xhr, status, thrown){
            // error json file
            bar_jsonfeed = [];
            bar_jsonfeed_iglk = [];
            console.log(status);
            console.log(thrown);
        }
    });

    var settings = setEventSettings('玩家留存率（最高进度-包含跳转）', bar_jsonfeed, 28, 70);
    var settings_iglk = setEventSettings('玩家留存率（最高进度-排除跳转）', bar_jsonfeed_iglk, 27, 69);
    
    // setup the chart
    $('#barChartEvent').jqxChart(settings);
    $('#barChartEvent_iglk').jqxChart(settings_iglk);
}

function drawBarChartQuality() {
	
    var bar_jsonfeed = new Array();

    // get the dataAdapter for source in settings
    $.ajax({
        type: 'GET',
        url: 'data/quality.json',
        dataType: 'json',
        async: false,
        cache: false,
        success: function(responseJSON){  
            $.each(responseJSON,function(i,item){

                var percentage = 0;
                var pie_jsonfeed = new Array();
                var $sum = parseInt(item.quality[0].value) + parseInt(item.quality[1].value) + parseInt(item.quality[2].value) + parseInt(item.quality[3].value)
                
                bar_jsonfeed.push(
                    {
                        '阶段' : item.period,
                        '流畅' : parseInt(item.quality[0].value),
                        '标准' : parseInt(item.quality[1].value),
                        '优质' : parseInt(item.quality[2].value),
                        '精美' : parseInt(item.quality[3].value)
                    }
                );
                
                for(var j=0; j<item.quality.length; j++){

                    if($sum != 0) {
                        percentage = (parseFloat(parseInt(item.quality[j].value)/$sum)*100).toFixed(2)
                    }

                    pie_jsonfeed.push(
                        {
                            '阶段' : item.period,
                            '画质' : item.quality[j].name,
                            '百分比' : percentage
                        }              
                    );
                }

                drawPieChartQuality(i, item.period, pie_jsonfeed);
            })
        },
        error: function (xhr, status, thrown){
            // error json file
            bar_jsonfeed = [
                {
                    '阶段' : '数据错误',
                    '流畅' : 0,
                    '标准' : 0,
                    '优质' : 0,
                    '精美' : 0
                }
            ];
            console.log(status);
            console.log(thrown);
        }
    });

    var settings = {
        title: '画质分布',
        description: '',
        enableAnimations: true,
        showLegend: true,
        padding: { left: 40, top: 10, right: 40, bottom: 40 },
        titlePadding: { left: 90, top: 15, right: 0, bottom: 20 },
        source: bar_jsonfeed,
        xAxis:
            {
                dataField: '阶段',
                showTickMarks: true,
                tickMarksInterval: 1,
                tickMarksColor: '#888888',
                unitInterval: 1,
                showGridLines: true,
                gridLinesInterval: 1,
                gridLinesColor: '#888888',
                axisSize: 'auto',
                flip: false
            },
        colorScheme: 'scheme05',
        seriesGroups:
            [
                {
                    type: 'column',
                    columnsGapPercent: 100,
                    //click: barChartSeverityHandler,
                    valueAxis:
                    {
                        unitInterval: 10,
                        minValue: 0,
                        displayValueAxis: true,
                        description: '',
                        tickMarksColor: '#888888',
                        showTickMarks: false,
                        //flip: true
                    },
                    series: [
                            { dataField: '流畅', displayText: '流畅', showLabels: true },
                            { dataField: '标准', displayText: '标准', showLabels: true },
                            { dataField: '优质', displayText: '优质', showLabels: true },
                            { dataField: '精美', displayText: '精美', showLabels: true }
                    ]
                }
            ]
    };
    // setup the chart
    $('#barChartQuality').jqxChart(settings);
}

function drawPieChartQuality(i, title, jsonfeed) {

    var settings = {
        title: title,
        description: '',
        enableAnimations: true,
        showLegend: true,
        showBorderLine: true,
        legendLayout: { left: 40, top: 320, width: 0, height: 0},
        padding: { left: 0, top: 0, right: 0, bottom: 0 },
        titlePadding: { left: 0, top: 20, right: 0, bottom: 0 },
        source: jsonfeed,
        colorScheme: 'scheme05',
        seriesGroups:
            [
                {
                    type: 'pie',
                    showLabels: true,
                    series:
                        [
                            { 
                                dataField: '百分比',
                                displayText: '画质',
                                labelRadius: 95,
                                initialAngle: 0,
                                radius: 78,
                                centerOffset: 2,
                                formatFunction: function (value) {
                                    if (isNaN(value))
                                        return value;
                                    return parseFloat(value) + '%';             
                                }
                            }
                        ]
                }
            ]
    };
    
    // setup the chart
    $('#pieChartQuality_'+i).jqxChart(settings);
}

function drawBarChartFps() {
	
    var bar_jsonfeed = new Array();
    
    // get the dataAdapter for source in settings
    $.ajax({
        type: 'GET',
        url: 'data/fps.json',
        dataType: 'json',
        async: false,
        cache: false,
        success: function(responseJSON){
            
            $.each(responseJSON,function(i,item){

                var percentage = 0;
                var pie_jsonfeed = new Array();
                var $sum = parseInt(item.fps[0].value) + parseInt(item.fps[1].value) + parseInt(item.fps[2].value) + parseInt(item.fps[3].value)
                           + parseInt(item.fps[4].value) + parseInt(item.fps[5].value) + parseInt(item.fps[6].value) + parseInt(item.fps[7].value)
                           + parseInt(item.fps[8].value) + parseInt(item.fps[9].value) + parseInt(item.fps[10].value) + parseInt(item.fps[11].value)
                           + parseInt(item.fps[12].value);

                bar_jsonfeed.push(
                    {
                        '阶段' : item.period,
                        '0-5' : parseInt(item.fps[0].value),
                        '5-10' : parseInt(item.fps[1].value),
                        '10-15' : parseInt(item.fps[2].value),
                        '15-20' : parseInt(item.fps[3].value),
                        '20-25' : parseInt(item.fps[4].value),
                        '25-30' : parseInt(item.fps[5].value),
                        '30-35' : parseInt(item.fps[6].value),
                        '35-40' : parseInt(item.fps[7].value),
                        '40-45' : parseInt(item.fps[8].value),
                        '45-50' : parseInt(item.fps[9].value),
                        '50-55' : parseInt(item.fps[10].value),
                        '55-60' : parseInt(item.fps[11].value),
                        '60以上' : parseInt(item.fps[12].value)
                    }
                );

                for(var j=0; j<item.fps.length; j++){

                    if($sum != 0) {
                        percentage = (parseFloat(parseInt(item.fps[j].value)/$sum)*100).toFixed(2)
                    }

                    pie_jsonfeed.push(
                        {
                            '阶段' : item.period,
                            '帧率' : item.fps[j].name,
                            '百分比' : percentage
                        }              
                    );
                }
                
                drawPieChartFps(i, item.period, pie_jsonfeed);
            })
        },
        error: function (xhr, status, thrown){
            // error json file
            bar_jsonfeed = [
                {
                    '阶段' : '数据错误',
                    '0-5' : 0,
                    '5-10' : 0,
                    '10-15' : 0,
                    '15-20' : 0,
                    '20-25' : 0,
                    '25-30' : 0,
                    '30-35' : 0,
                    '35-40' : 0,
                    '40-45' : 0,
                    '45-50' : 0,
                    '50-55' : 0,
                    '55-60' : 0,
                    '60以上' : 0
                }
            ];
            console.log(status);
            console.log(thrown);
        }
    });

    var settings = {
        title: '帧率分布',
        description: '',
        enableAnimations: true,
        showLegend: true,
        padding: { left: 40, top: 10, right: 40, bottom: 40 },
        titlePadding: { left: 90, top: 15, right: 0, bottom: 20 },
        source: bar_jsonfeed,
        xAxis:
            {
                dataField: '阶段',
                showTickMarks: true,
                tickMarksInterval: 1,
                tickMarksColor: '#888888',
                unitInterval: 1,
                showGridLines: true,
                gridLinesInterval: 1,
                gridLinesColor: '#888888',
                axisSize: 'auto',
                flip: false
            },
        //colorScheme: 'scheme01',
        seriesGroups:
            [
                {
                    type: 'column',
                    columnsGapPercent: 150,
                    //click: barChartSeverityHandler,
                    valueAxis:
                    {
                        unitInterval: 2,
                        minValue: 0,
                        displayValueAxis: true,
                        description: '',
                        tickMarksColor: '#888888',
                        showTickMarks: false,
                        //flip: true
                    },
                    series: [
                            { dataField: '0-5', displayText: '0-5', showLabels: true, color: fps_bar_color_1 },
                            { dataField: '5-10', displayText: '5-10', showLabels: true, color: fps_bar_color_2 },
                            { dataField: '10-15', displayText: '10-15', showLabels: true, color: fps_bar_color_3 },
                            { dataField: '15-20', displayText: '15-20', showLabels: true, color: fps_bar_color_4 },
                            { dataField: '20-25', displayText: '20-25', showLabels: true, color: fps_bar_color_5 },
                            { dataField: '25-30', displayText: '25-30', showLabels: true, color: fps_bar_color_6 },
                            { dataField: '30-35', displayText: '30-35', showLabels: true, color: fps_bar_color_7 },
                            { dataField: '35-40', displayText: '35-40', showLabels: true, color: fps_bar_color_8 },
                            { dataField: '40-45', displayText: '40-45', showLabels: true, color: fps_bar_color_9 },
                            { dataField: '45-50', displayText: '45-50', showLabels: true, color: fps_bar_color_10 },
                            { dataField: '50-55', displayText: '50-55', showLabels: true, color: fps_bar_color_11 },
                            { dataField: '55-60', displayText: '55-60', showLabels: true, color: fps_bar_color_12 },
                            { dataField: '60以上', displayText: '60以上', showLabels: true, color: fps_bar_color_13 }
                    ]
                }
            ]
    };
    // setup the chart
    $('#barChartFps').jqxChart(settings);
}

function drawPieChartFps(i, title, jsonfeed) {

    var settings = {
        title: title,
        description: '',
        enableAnimations: true,
        showLegend: true,
        showBorderLine: true,
        //legendLayout: { left: 40, top: 250, width: 0, height: 0},
        padding: { left: 0, top: 0, right: 0, bottom: 0 },
        titlePadding: { left: 0, top: 20, right: 0, bottom: 0 },
        source: jsonfeed,
        //colorScheme: 'scheme01',
        seriesGroups:
            [
                {
                    type: 'pie',
                    showLabels: true,
                    series:
                        [
                            { 
                                dataField: '百分比',
                                displayText: '帧率',
                                labelRadius: 95,
                                initialAngle: 0,
                                radius: 78,
                                centerOffset: 3,
                                formatFunction: function (value) {
                                    if (isNaN(value))
                                        return value;
                                    return parseFloat(value) + '%';             
                                },
                                colorFunction: function (value, itemIndex, serie, group) { 
                                    switch (itemIndex) { 
                                        case 0: return fps_bar_color_1; 
                                        case 1: return fps_bar_color_2; 
                                        case 2: return fps_bar_color_3; 
                                        case 3: return fps_bar_color_4; 
                                        case 4: return fps_bar_color_5;
                                        case 5: return fps_bar_color_6;
                                        case 6: return fps_bar_color_7;
                                        case 7: return fps_bar_color_8;
                                        case 8: return fps_bar_color_9;
                                        case 9: return fps_bar_color_10;
                                        case 10: return fps_bar_color_11;
                                        case 11: return fps_bar_color_12;
                                        case 12: return fps_bar_color_13;
                                        case 13: return fps_bar_color_14;
                                    }
                                }
                            }
                        ]
                }
            ]
    };
    
    // setup the chart
    $('#pieChartFps_'+i).jqxChart(settings);
}

function drawBarChartMemory() {
	
    var bar_jsonfeed = new Array();
    
    // get the dataAdapter for source in settings
    $.ajax({
        type: 'GET',
        url: 'data/memory.json',
        dataType: 'json',
        async: false,
        cache: false,
        success: function(responseJSON){
            
            $.each(responseJSON,function(i,item){
                
                bar_jsonfeed.push(
                    {
                        '阶段' : item.period,
                        '0-50' : parseInt(item.memory[0].value),
                        '50-100' : parseInt(item.memory[1].value),
                        '100-150' : parseInt(item.memory[2].value),
                        '150-200' : parseInt(item.memory[3].value),
                        '200-250' : parseInt(item.memory[4].value),
                        '250-300' : parseInt(item.memory[5].value),
                        '300-350' : parseInt(item.memory[6].value),
                        '350-400' : parseInt(item.memory[7].value),
                        '400-450' : parseInt(item.memory[8].value),
                        '450-500' : parseInt(item.memory[9].value),
                        '500-550' : parseInt(item.memory[10].value),
                        '550-600' : parseInt(item.memory[11].value),
                        '600以上' : parseInt(item.memory[12].value)
                    }
                );
                
                var percentage = 0;
                var pie_jsonfeed = new Array();
                var $sum = parseInt(item.memory[0].value) + parseInt(item.memory[1].value) + parseInt(item.memory[2].value) + parseInt(item.memory[3].value)
                           + parseInt(item.memory[4].value) + parseInt(item.memory[5].value) + parseInt(item.memory[6].value) + parseInt(item.memory[7].value)
                           + parseInt(item.memory[8].value) + parseInt(item.memory[9].value) + parseInt(item.memory[10].value) + parseInt(item.memory[11].value)
                           + parseInt(item.memory[12].value);

                for(var j=0; j<item.memory.length; j++){

                    if($sum != 0) {
                        percentage = (parseFloat(parseInt(item.memory[j].value)/$sum)*100).toFixed(2)
                    }

                    pie_jsonfeed.push(
                        {
                            '阶段' : item.period,
                            '内存' : item.memory[j].name,
                            '百分比' : percentage
                        }              
                    );
                }

                drawPieChartMemory(i, item.period, pie_jsonfeed);

            })
        },
        error: function (xhr, status, thrown){
            // error json file
            bar_jsonfeed = [
                {
                    '阶段' : '数据错误',
                    '0-50' : 0,
                    '50-100' : 0,
                    '100-150' : 0,
                    '150-200' : 0,
                    '200-250' : 0,
                    '250-300' : 0,
                    '300-350' : 0,
                    '350-400' : 0,
                    '400-450' : 0,
                    '450-500' : 0,
                    '500-550' : 0,
                    '550-600' : 0,
                    '600以上' : 0
                }
            ];
            console.log(status);
            console.log(thrown);
        }
    });

    var settings = {
        title: '内存分布',
        description: '',
        enableAnimations: true,
        showLegend: true,
        padding: { left: 40, top: 10, right: 40, bottom: 40 },
        titlePadding: { left: 90, top: 15, right: 0, bottom: 20 },
        source: bar_jsonfeed,
        xAxis:
            {
                dataField: '阶段',
                showTickMarks: true,
                tickMarksInterval: 1,
                tickMarksColor: '#888888',
                unitInterval: 1,
                showGridLines: true,
                gridLinesInterval: 1,
                gridLinesColor: '#888888',
                axisSize: 'auto',
                flip: false
            },
        //colorScheme: 'scheme01',
        seriesGroups:
            [
                {
                    type: 'column',
                    columnsGapPercent: 150,
                    //click: barChartSeverityHandler,
                    valueAxis:
                    {
                        unitInterval: 5,
                        minValue: 0,
                        displayValueAxis: true,
                        description: '',
                        tickMarksColor: '#888888',
                        showTickMarks: false,
                        //flip: true
                    },
                    series: [
                            { dataField: '0-50', displayText: '0-50', showLabels: true, color: memory_bar_color_1 },
                            { dataField: '50-100', displayText: '50-100', showLabels: true, color: memory_bar_color_2 },
                            { dataField: '100-150', displayText: '100-150', showLabels: true, color: memory_bar_color_3 },
                            { dataField: '150-200', displayText: '150-200', showLabels: true, color: memory_bar_color_4 },
                            { dataField: '200-250', displayText: '200-250', showLabels: true, color: memory_bar_color_5 },
                            { dataField: '250-300', displayText: '250-300', showLabels: true, color: memory_bar_color_6 },
                            { dataField: '300-350', displayText: '300-350', showLabels: true, color: memory_bar_color_7 },
                            { dataField: '350-400', displayText: '350-400', showLabels: true, color: memory_bar_color_8 },
                            { dataField: '400-450', displayText: '400-450', showLabels: true, color: memory_bar_color_9 },
                            { dataField: '450-500', displayText: '450-500', showLabels: true, color: memory_bar_color_10 },
                            { dataField: '500-550', displayText: '500-550', showLabels: true, color: memory_bar_color_11 },
                            { dataField: '550-600', displayText: '550-600', showLabels: true, color: memory_bar_color_12 },
                            { dataField: '600以上', displayText: '600以上', showLabels: true, color: memory_bar_color_13 }
                    ]
                }
            ]
    };
    // setup the chart
    $('#barChartMemory').jqxChart(settings);
}

function drawPieChartMemory(i, title, jsonfeed) {

    var settings = {
        title: title,
        description: '',
        enableAnimations: true,
        showLegend: true,
        showBorderLine: true,
        //legendLayout: { left: 40, top: 250, width: 0, height: 0},
        padding: { left: 0, top: 0, right: 0, bottom: 0 },
        titlePadding: { left: 0, top: 20, right: 0, bottom: 0 },
        source: jsonfeed,
        //colorScheme: 'scheme01',
        seriesGroups:
            [
                {
                    type: 'pie',
                    showLabels: true,
                    series:
                        [
                            { 
                                dataField: '百分比',
                                displayText: '内存',
                                labelRadius: 95,
                                initialAngle: 0,
                                radius: 78,
                                centerOffset: 2,
                                formatFunction: function (value) {
                                    if (isNaN(value))
                                        return value;
                                    return parseFloat(value) + '%';             
                                },
                                colorFunction: function (value, itemIndex, serie, group) { 
                                    switch (itemIndex) { 
                                        case 0: return memory_bar_color_1; 
                                        case 1: return memory_bar_color_2; 
                                        case 2: return memory_bar_color_3; 
                                        case 3: return memory_bar_color_4; 
                                        case 4: return memory_bar_color_5;
                                        case 5: return memory_bar_color_6;
                                        case 6: return memory_bar_color_7;
                                        case 7: return memory_bar_color_8;
                                        case 8: return memory_bar_color_9;
                                        case 9: return memory_bar_color_10;
                                        case 10: return memory_bar_color_11;
                                        case 11: return memory_bar_color_12;
                                        case 12: return memory_bar_color_13;
                                        case 13: return memory_bar_color_14;
                                    }
                                }
                            }
                        ]
                }
            ]
    };
    
    // setup the chart
    $('#pieChartMemory_'+i).jqxChart(settings);
}


// define click handler for each chart
function pieChartTopNHandler(e) {
    window.open("data/pieChartTopN.html#assignee" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}

function barChartSeverityHandler(e) {
    window.open("data/barChartSeverity.html#severity" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}

function barChartOverOneYearBySeverityHandler(e){
	window.open("data/barChartOverOneYearBySeverity.html#severity" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}

function chartMonthHandler(e) {
    window.open("data/chartMonth.html#month" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}

function chartAllBugsCreatedByMonthHandler(e) {
    window.open("data/chartAllBugsCreatedInSixMonthsByMonth.html#created%20month" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}

function chartAllBugsClosedByMonthHandler(e) {
    window.open("data/chartAllBugsClosedInSixMonthsByMonth.html#closed%20month" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}
function chartsOpenBugsCreatedByMonthHandler(e) {
    window.open("data/chartOpenBugsCreatedInSixMonthsByMonth.html#closed%20month%20open" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}
function chartTagHandler(e) {
    window.open("data/chartTag.html#tag" + e.elementIndex, "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
}

// define image convert server address
function getExportServer() {
    return 'http://www.jqwidgets.com/export_server/export.php';
}

// generate html content
function generateHTML(filename, content) {
    return pageContent = 
        '<!DOCTYPE html>' +
        '<html>' +
        '<head>' +
        '<link rel="stylesheet" href="http://www.jqwidgets.com/jquery-widgets-demo/jqwidgets/styles/jqx.base.css" type="text/css" />' +
        '<meta charset="utf-8" />' +
        '<title>' + filename + '</title>' +
        '</head>' +
        '<body>' + content + '</body></html>';
}

// export all charts
function exportAllCharts() {
    $("#export").jqxButton({});

    $("#export").click(function () {
        var content = $('#pieChartTopN')[0].outerHTML;
        content = content + $('#barChartSeverity')[0].outerHTML;
        content = content + $('#chartMonth')[0].outerHTML;
        content = content + $('#chartTag')[0].outerHTML;     
        var newWindow = window.open('', '', 'width=970, height=720, scrollbars=yes, menubar=yes, status=1'),
        document = newWindow.document.open(),
        pageContent = generateHTML('result', content);
        document.write(pageContent);
        document.close();
    });
}

// notify nobody assignee bugs
function notifyNobodyBugs() {

    var num_nobody = 0;
   
    $.ajax({
        type: 'GET',
        url: 'data/NobodyAssigneeBugsList.xml',
        dataType: 'xml',
        async: false,
        cache: false,
        success: function(responseXML) {
            num_nobody = parseInt($(responseXML).find('total').text());
        },
        error: function (xhr, status, thrown){
            num_nobody = 0;
            console.log(status);
            console.log(thrown);
        }
    });

    if (num_nobody != 0) {
        if (num_nobody == 1) {
            $('#num_nobody').text(num_nobody + " nobody assignee bug!");
        } else {
            $('#num_nobody').text(num_nobody + " nobody assignee bugs!");
        }
        
        $('#tip').text("Click to view.");
        
        $("#jqxNotification").jqxNotification({ width: "auto", position: "bottom-right", opacity: 0.7, autoOpen: true,
            closeOnClick: true, autoClose: false, showCloseButton: true, template: "warning", blink: true
        });

        $("#jqxNotification").on('click', function () {
            window.open("data/NobodyAssigneeBugsList.html", "_black", "toolbar=yes, scrollbars=yes, resizable=yes, top=0, left=0, width=1000, height=1000");
        });
    }
}

// draw all charts
function drawChartsAndGrids() {
    try {
        //drawDataTableTableEvent();
        drawBarChartEvent();
        drawBarChartQuality();
        drawBarChartFps();
        drawBarChartMemory();
        //drawBarChartOverOneYearBySeverity();
        //drawChartMonth();
        //drawChartAllBugsCreatedAndClosedInSixMonthsByMonth();
        //drawChartTag();
        //exportAllCharts();
        //notifyNobodyBugs();
        //$('#export').tooltip().on("mouseenter", function () {
        //    var $this = $(this), tooltip = $this.next(".tooltip");
        //    tooltip.find(".tooltip-inner").css({
        //        backgroundColor: "#000000",
        //        color: "#ffffff",
        //        borderColor: "#333",
        //        borderWidth: "1px",
        //        borderStyle: "solid"
         //   });
        //});
    } catch(err) {
    }
}