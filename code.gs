// Code.gs

// 스프레드시트가 열릴 때 메뉴 생성
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('웹툰 관리자')
    .addItem('앱 실행', 'showWebApp')
    .addToUi();
}

// 메뉴 클릭 시 웹 앱 실행
function showWebApp() {
  const html = HtmlService.createHtmlOutputFromFile('index')
    .setWidth(1000)
    .setHeight(800);
  SpreadsheetApp.getUi().showModalDialog(html, '웹툰 관리자');
}

// 웹 앱 접속 시 데이터 로딩
function doGet(e) {
  const template = HtmlService.createTemplateFromFile('index');
  template.webtoonData = JSON.stringify(getWebtoonData()); // 시트 데이터를 JSON 문자열로 변환하여 전달
  return template.evaluate()
    .setTitle('웹툰 관리자')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0');
}

/**
 * 'Webtoons' 시트에서 모든 데이터를 읽어와 객체 배열 형태로 반환합니다.
 * @returns {Array<Object>} 웹툰 데이터 객체의 배열
 */
function getWebtoonData() {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Webtoons');
    if (!sheet) return [];
    
    const range = sheet.getDataRange();
    const values = range.getValues();
    
    if (values.length < 2) return []; // 헤더만 있거나 비어있으면 빈 배열 반환

    const headers = values.shift(); // 첫 행을 헤더로 사용
    
    return values.map(row => {
      const webtoon = {};
      headers.forEach((header, index) => {
        // 'episodes'는 숫자로 변환
        webtoon[header] = (header === 'episodes') ? Number(row[index]) : row[index];
      });
      return webtoon;
    });
  } catch (e) {
    console.error("데이터 로드 실패: " + e);
    return [];
  }
}

/**
 * 클라이언트에서 받은 ID 목록과 일치하는 행을 시트에서 삭제합니다.
 * @param {Array<String>} idsToDelete 삭제할 웹툰 ID의 배열
 * @returns {String} 작업 완료 메시지
 */
function deleteRowsByIds(idsToDelete) {
  try {
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Webtoons');
    if (!sheet) return "시트를 찾을 수 없습니다.";

    const idsSet = new Set(idsToDelete.map(String)); // 비교를 위해 Set 사용
    const data = sheet.getDataRange().getValues();
    const idColumnIndex = data[0].indexOf('id');

    if (idColumnIndex === -1) return "'id' 열을 찾을 수 없습니다.";

    // 행을 삭제하면 인덱스가 바뀌므로, 뒤에서부터 삭제를 진행해야 안전합니다.
    for (let i = data.length - 1; i >= 1; i--) {
      const currentId = String(data[i][idColumnIndex]);
      if (idsSet.has(currentId)) {
        sheet.deleteRow(i + 1); // getValues()는 0-based, deleteRow()는 1-based
      }
    }
    return "선택된 항목이 삭제되었습니다.";
  } catch(e) {
    console.error("삭제 작업 실패: " + e);
    return "오류가 발생하여 삭제하지 못했습니다.";
  }
}