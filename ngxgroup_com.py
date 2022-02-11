import datetime
import hashlib
import json
import re

# from geopy import Nominatim

from src.bstsouecepkg.extract import Extract
from src.bstsouecepkg.extract import GetPages


class Handler(Extract, GetPages):
    base_url = 'https://ngxgroup.com'
    NICK_NAME = base_url.split('//')[-1]
    fields = ['overview', 'officership', 'documents', 'Financial_Information']
    overview = {}
    tree = None
    api = None

    header = {
        'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9;application/json;application/json;odata=verbose',
        'accept-language': 'en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7',
        'Content-Type': 'application/json; application/x-www-form-urlencoded; charset=UTF-8'
    }

    def getpages(self, searchquery):
        result = []
        # self.tree = self.get_tree('https://doclib.ngxgroup.com/REST/api/issuers/companydirectory?$orderby=CompanyName', headers=self.header)
        self.get_working_tree_api('https://doclib.ngxgroup.com/REST/api/issuers/companydirectory?$orderby=CompanyName', 'api')
        'https://ngxgroup.com/exchange/data/company-profile/?isin=NGACCESS0005&directory=companydirectory'
        #print(self.api)
        for company in self.api:
            if searchquery.lower() in company['CompanyName'].lower():
                result.append(company)
        return result

    def get_by_xpath(self, xpath):
        try:
            el = self.tree.xpath(xpath)
        except Exception as e:
            print(e)
            return None
        if el:
            if type(el) == str or type(el) == list:
                el = [i.strip() for i in el]
                el = [i for i in el if i != '']
            if len(el) > 1 and type(el) == list:
                el = list(dict.fromkeys(el))
            return el
        else:
            return None

    def reformat_date(self, date, format):
        date = datetime.datetime.strptime(date.strip(), format).strftime('%Y-%m-%d')
        return date

    def fill_business_classifier(self, xpathCodes=None, xpathDesc=None, xpathLabels=None, api=False):
        res = []
        length = None
        codes, desc, labels = None, None, None

        if xpathCodes:
            codes = self.get_by_xpath(xpathCodes) if not api else [self.get_by_api(xpathCodes)]
            if codes:
                length = len(codes)
        if xpathDesc:
            desc = self.get_by_xpath(xpathDesc) if not api else [self.get_by_api(xpathDesc)]
            if desc:
                length = len(desc)
        if xpathLabels:
            labels = self.get_by_xpath(xpathLabels) if not api else [self.get_by_api(xpathLabels)]
            if labels:
                length = len(labels)

        if length:
            for i in range(length):
                temp = {
                    'code': codes[i] if codes else '',
                    'description': desc[i] if desc else '',
                    'label': labels[i] if labels else ''
                }
                res.append(temp)
        if res:
            self.overview['bst:businessClassifier'] = res

    def get_post_addr(self, tree):
        addr = self.get_by_xpath(tree, '//span[@id="lblMailingAddress"]/..//text()', return_list=True)
        if addr:
            addr = [i for i in addr if
                    i != '' and i != 'Mailing Address:' and i != 'Inactive' and i != 'Registered Office outside NL:']
            if addr[0] == 'No address on file':
                return None
            if addr[0] == 'Same as Registered Office' or addr[0] == 'Same as Registered Office in NL':
                return 'Same'
            fullAddr = ', '.join(addr)
            temp = {
                'fullAddress': fullAddr if 'Canada' in fullAddr else (fullAddr + ' Canada'),
                'country': 'Canada',

            }
            replace = re.findall('[A-Z]{2},\sCanada,', temp['fullAddress'])
            if not replace:
                replace = re.findall('[A-Z]{2},\sCanada', temp['fullAddress'])
            if replace:
                torepl = replace[0].replace(',', '')
                temp['fullAddress'] = temp['fullAddress'].replace(replace[0], torepl)
            try:
                zip = re.findall('[A-Z]\d[A-Z]\s\d[A-Z]\d', fullAddr)
                if zip:
                    temp['zip'] = zip[0]
            except:
                pass
        # print(addr)
        # print(len(addr))
        if len(addr) == 4:
            temp['city'] = addr[-3]
            temp['streetAddress'] = addr[0]
        if len(addr) == 5:
            temp['city'] = addr[-4]
            temp['streetAddress'] = addr[0]
        if len(addr) == 6:
            temp['city'] = addr[-4]
            temp['streetAddress'] = ', '.join(addr[:2])

        return temp

    def get_address(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.get_by_xpath(xpath)
        if key:
            addr = self.get_by_api(key)
        if addr:
            if type(addr) == list:
                addr = ', '.join(addr)
            if '\n' in addr:
                splitted_addr = addr.split('\n')
            if ', ' in addr:
                splitted_addr = addr.split(', ')

            addr = addr.replace('\n', ' ')
            addr = addr[0] if type(addr) == list else addr
            temp = {
                'fullAddress': addr,
                'country': 'Nigeria'
            }
            if zipPattern:
                zip = re.findall(zipPattern, addr)
                if zip:
                    temp['zip'] = zip[0]
            try:
                patterns = ['Suite\s\d+']
                for pattern in patterns:
                    pat = re.findall(pattern, addr)
                    if pat:
                        first_part = addr.split(pat[0])
                        temp['streetAddress'] = first_part[0] + pat[0]
            except:
                pass
            try:
                street = addr.split('Street')
                if len(street) == 2:
                    temp['streetAddress'] = street[0] + 'Street'
                temp['streetAddress'] = addr.split(',')[0]


                # if temp['streetAddress']:
                #     temp['streetAddress'] = splitted_addr[0]
            except:
                pass
            try:
                # city = addr.replace(temp['zip'], '')
                # city = city.replace(temp['streetAddress'], '')
                # city = city.replace(',', '').strip()
                # city = re.findall('[A-Z][a-z]+', city)
                temp['city'] = addr.split(', ')[-1].replace('.', '')
                # temp['fullAddress'] += f", {temp['city']}"
            except:
                pass
            temp['fullAddress'] += f', {temp["country"]}'
            #temp['country'] = 'Nigeria'

            temp['fullAddress'] = temp['fullAddress'].replace('.,', ',')
            if returnAddress:
                return temp
            self.overview['mdaas:RegisteredAddress'] = temp

    def get_prev_names(self, tree):
        prev = []
        names = self.get_by_xpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[1]/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[1]/text()',
                                  return_list=True)
        dates = self.get_by_xpath(tree,
                                  '//table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="row"]//td[2]/span/text() | //table[@id="tblPreviousCompanyNames"]//tr[@class="row"]//tr[@class="rowalt"]//td[2]/span/text()',
                                  return_list=True)
        print(names)
        if names:
            names = [i for i in names if i != '']
        if names and dates:
            for name, date in zip(names, dates):
                temp = {
                    'name': name,
                    'valid_to': date
                }
                prev.append(temp)
        return prev

    def get_by_api(self, key):
        try:
            el = self.api[key]
            return el
        except:
            return None

    def fillField(self, fieldName, key=None, xpath=None, test=False, reformatDate=None):
        if xpath:
            el = self.get_by_xpath(xpath)
        if key:
            el = self.get_by_api(key)
        if test:
            print(el)
        if el:
            if len(el) == 1:
                el = el[0]
            el = self.reformat_date(el, reformatDate) if reformatDate else el
            if fieldName == 'vcard:organization-name':
                self.overview[fieldName] = el.split('(')[0].strip()

            if fieldName == 'hasActivityStatus':
                self.overview[fieldName] = el

            if fieldName == 'bst:registrationId':
                self.overview[fieldName] = el

            if fieldName == 'Service':
                self.overview[fieldName] = {'serviceType': el}

            if fieldName == 'vcard:organization-tradename':
                self.overview[fieldName] = el.split('\n')[0].strip()

            if fieldName == 'bst:aka':
                names = el.split('\n')
                names = el.split(' D/B/A ')
                if len(names) > 1:
                    names = [i.strip() for i in names]
                    self.overview[fieldName] = names
                else:
                    self.overview[fieldName] = names

            if fieldName == 'lei:legalForm':
                self.overview[fieldName] = {
                    'code': '',
                    'label': el}


            if fieldName == 'map':
                self.overview[fieldName] = el[0] if type(el) == list else el

            if fieldName == 'previous_names':
                el = el.strip()
                el = el.split('\n')
                if len(el) < 1:
                    self.overview[fieldName] = {'name': [el[0].strip()]}
                else:
                    el = [i.strip() for i in el]
                    res = []
                    for i in el:
                        temp = {
                            'name': i
                        }
                        res.append(temp)
                    self.overview[fieldName] = res

            if fieldName == 'isIncorporatedIn':
                if reformatDate:
                    self.overview[fieldName] = self.reformat_date(el, reformatDate)
                else:
                    self.overview[fieldName] = el.split('T')[0]

            if fieldName == 'sourceDate':
                self.overview[fieldName] = self.reformat_date(el, '%d.%m.%Y')
            if fieldName == 'regExpiryDate':
                self.overview[fieldName] = el

            if fieldName == 'bst:description':
                self.overview[fieldName] = el

            if fieldName == 'hasURL' and el != 'http://':
                if 'http:' not in el:
                    el = 'http://' + el
                self.overview[fieldName] = el
            if fieldName == 'bst:email':
                self.overview['bst:email'] = el

            if fieldName == 'tr-org:hasRegisteredPhoneNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.overview[fieldName] = el

            if fieldName == 'agent':
                # print(el)
                self.overview[fieldName] = {
                    'name': el.split('\n')[0],
                    'mdaas:RegisteredAddress': self.get_address(returnAddress=True, addr=' '.join(el.split('\n')[1:]),
                                                                zipPattern='[A-Z]\d[A-Z]\s\d[A-Z]\d')
                }
            if fieldName == 'RegulationStatusEffectiveDate':
                self.overview['RegulationStatusEffectiveDate'] = el

            if fieldName == 'logo':
                self.overview['logo'] = 'https://m.bvb.ro/FinancialInstruments/Details/' + el

            if fieldName== 'hasRegisteredFaxNumber':
                if type(el) == list and len(el) > 1:
                    el = el[0]
                self.overview[fieldName] = el



    def fill_identifiers(self, xpathTradeRegistry=None, xpathOtherCompanyId=None, xpathInternationalSecurIdentifier=None, xpathLegalEntityIdentifier=None):
        try:
            temp = self.overview['identifiers']
        except:
            temp = {}

        if xpathTradeRegistry:
            trade = self.get_by_xpath(xpathTradeRegistry)
            if trade:
                temp['trade_register_number'] = re.findall('HR.*', trade[0])[0]
        if xpathOtherCompanyId:
            other = self.get_by_xpath(xpathOtherCompanyId)
            if other:
                temp['other_company_id_number'] = other[0]
        if xpathInternationalSecurIdentifier:
            el = self.get_by_xpath(xpathInternationalSecurIdentifier)
            temp['international_securities_identifier'] = el[0]
        if xpathLegalEntityIdentifier:
            el = self.get_by_xpath(xpathLegalEntityIdentifier)
            temp['legal_entity_identifier'] = el[0]


        if temp:
            self.overview['identifiers'] = temp

    def check_tree(self):
        print(self.tree.xpath('//text()'))

    def get_working_tree_api(self, link_name, type, method='GET', data=None):
        if type == 'tree':
            if data:
                self.tree = self.get_tree(link_name,
                                          headers=self.header, method=method, data=data)
            else:
                self.tree = self.get_tree(link_name,
                                          headers=self.header, method=method)
        if type == 'api':
            if data:
                self.api = self.get_content(link_name,
                                            headers=self.header, method=method, data=json.dumps(data))
            else:
                self.api = self.get_content(link_name,
                                        headers=self.header, method=method)
            self.api = json.loads(self.api.content)

    def fillRatingSummary(self, xpathRatingGroup=None, xpathRatings=None):
        temp = {}
        if xpathRatingGroup:
            group = self.get_by_xpath(xpathRatingGroup)
            if group:
                temp['rating_group'] = group[0]
        if xpathRatings:
            rating = self.get_by_xpath(xpathRatings)
            if rating:
                temp['ratings'] = rating[0].split(' ')[0]
        if temp:
            self.overview['rating_summary'] = temp

    def fillAgregateRating(self, xpathReview=None, xpathRatingValue=None):
        temp = {}
        if xpathReview:
            review = self.get_by_xpath(xpathReview)
            if review:
                temp['reviewCount'] = review[0].split(' ')[0]
        if xpathRatingValue:
            value = self.get_by_xpath(xpathRatingValue)
            if value:
                temp['ratingValue'] = ''.join(value)

        if temp:
            temp['@type'] = 'aggregateRating'
            self.overview['aggregateRating'] = temp

    def fillReviews(self, xpathReviews=None, xpathRatingValue=None, xpathDate=None, xpathDesc=None):
        res = []
        try:
            reviews = self.tree.xpath(xpathReviews)
            for i in range(len(reviews)):
                temp = {}
                if xpathRatingValue:
                    ratingsValues = len(self.tree.xpath(f'//async-list//review[{i+1}]' + xpathRatingValue))
                    if ratingsValues:
                        temp['ratingValue'] = ratingsValues
                if xpathDate:
                    date = self.tree.xpath(f'//async-list//review[{i+1}]' + xpathDate)
                    if date:
                        temp['datePublished'] = date[0].split('T')[0]

                if xpathDesc:
                    desc = self.tree.xpath(f'//async-list//review[{i+1}]' + xpathDesc)
                    if desc:
                        temp['description'] = desc[0]
                if temp:
                    res.append(temp)
        except:
            pass
        if res:
            self.overview['review'] = res

    def fillRegulatorAddress(self, xpath=None, zipPattern=None, key=None, returnAddress=False, addr=None):
        if xpath:
            addr = self.get_by_xpath(xpath)[1:-2]
        if key:
            addr = self.get_by_api(key)
        if addr:
            if type(addr) == list:
                addr = ', '.join(addr)
            if '\n' in addr:
                splitted_addr = addr.split('\n')
            if ', ' in addr:
                splitted_addr = addr.split(', ')

            addr = addr.replace('\n', ' ')
            addr = addr[0] if type(addr) == list else addr
            temp = {
                'fullAddress': addr,
                'country': 'USA'
            }
            if zipPattern:
                zip = re.findall(zipPattern, addr)
                if zip:
                    temp['zip'] = zip[0]
            try:
                patterns = ['Suite\s\d+']
                for pattern in patterns:
                    pat = re.findall(pattern, addr)
                    if pat:
                        first_part = addr.split(pat[0])
                        temp['streetAddress'] = first_part[0] + pat[0]
            except:
                pass
            try:
                street = addr.split('Street')
                if len(street) == 2:
                    temp['streetAddress'] = street[0] + 'Street'
                temp['streetAddress'] = addr.split(',')[0]


                # if temp['streetAddress']:
                #     temp['streetAddress'] = splitted_addr[0]
            except:
                pass
            try:
                # city = addr.replace(temp['zip'], '')
                # city = city.replace(temp['streetAddress'], '')
                # city = city.replace(',', '').strip()
                # city = re.findall('[A-Z][a-z]+', city)
                temp['city'] = addr.split(', ')[-2].replace('.', '')
                # temp['fullAddress'] += f", {temp['city']}"
            except:
                pass
            temp['fullAddress'] += f', {temp["country"]}'
            temp['fullAddress'] = temp['fullAddress'].replace('.,', ',')
            if returnAddress:
                return temp
            self.overview['regulatorAddress'] = temp


    def getOfficerFromPage(self, link, officerType):
        self.get_working_tree_api(link, 'tree')
        temp = {}
        temp['name'] = self.get_by_xpath('//div[@class="form-group"]//strong[2]/text()')[0]

        temp['type'] = officerType
        addr = ','.join(self.get_by_xpath('//div[@class="MasterBorder"]//div[2]//div/text()')[:-1])
        if addr:
            temp['address'] = {
                'address_line_1': addr,
            }
            zip = re.findall('\d\d\d\d\d-\d\d\d\d', addr)[0]
            if zip:
                temp['address']['postal_code'] = zip
                temp['address']['address_line_1'] = addr.split(zip)[0]


        temp['officer_role'] = 'PRODUCER' if officerType == 'individual' else 'COMPANY'

        temp['status'] = self.get_by_xpath('//td//text()[contains(., "License Status")]/../../following-sibling::td//text()')[0]

        temp['information_source'] = self.base_url
        temp['information_provider'] = 'Idaho department of Insurance'
        return temp if temp['status'] == 'Active' else None

    def getHiddenValuesASP(self):
        names = self.get_by_xpath('//input[@type="hidden"]/@name')
        temp = {}
        for name in names:
            value = self.get_by_xpath(f'//input[@type="hidden"]/@name[contains(., "{name}")]/../@value')
            temp[name] = value[0] if value else ''
        return temp


    def get_overview(self, link_name):
        self.overview = {}
        self.api = link_name
        print(link_name)
        # self.get_working_tree_api(link_name, 'tree')
        #self.check_tree()
        try:
            self.fillField('vcard:organization-name', key='CompanyName')
        except:
            return None

        self.overview['isDomiciledIn'] = 'NG'

        try:
            self.overview['vcard:organization-tradename'] = f"{self.overview['vcard:organization-name']} ({self.get_by_api('Symbol')})"
        except:
            pass

        try:
            self.overview['bst:sourceLinks'] = [f'https://ngxgroup.com/exchange/data/company-profile/?isin={self.api["InternationSecIN"]}&directory=companydirectory']
        except:
            pass

        self.overview['hasActivityStatus'] = 'active'

        self.fillField('hasURL',
                       key='Website')

        self.fillField('bst:email',
                       key='Email')

        self.fillField('tr-org:hasRegisteredPhoneNumber',
                       key='Telephone')
        self.fillField('hasRegisteredFaxNumber',
                       key='Fax')

        self.fill_business_classifier(xpathDesc='Sector', xpathLabels='SubSector', api=True)

        self.get_address(key='CompanyAddress')

        self.overview['hasIPODate'] = self.api['DateListed'] if self.api['DateListed'] else '1970-01-01'

        self.fillField('isIncorporatedIn',
                       key='DateOfIncorporation')

        self.overview['bst:stock_info'] = {
            'mic_code': 'XNSA',
            'main_exchange': 'Nigerian Stock Exchange',
            'ticket_symbol': self.api['Symbol']
        }

        self.overview['bst:registryURI'] = self.overview['bst:sourceLinks'][0]
        self.overview['@source-id'] = self.NICK_NAME

        try:
            self.overview['Service'] = {
                'serviceType': self.api['NatureofBusiness']
            }
        except:
            pass

        try:
            self.overview['classOfShares'] = [{
                'class': 'outstandingShares',
                'count': str(self.api['SharesOutstanding']),
                'year': self.api['HIGH52WK_DATETIME'][:4]
            }]
        except:
            pass


















        # print(self.overview)
        # exit()
        #
        # self.fill_identifiers(xpathInternationalSecurIdentifier='//td//text()[contains(., "ISIN:")]/../following-sibling::td//text()',
        #                       )
        #
        #
        #
        #
        #
        # self.fillField('logo', xpath='//img[@id="ctl00_body_HeaderControl_imglogo"]/@src')
        # self.overview['bst:sourceLinks'] = [link_name]
        # self.fillField('hasActivityStatus',
        #                xpath='//td//text()[contains(., "Status:")]/../following-sibling::td//text()')
        #
        #
        # issueTab = self.get_by_xpath('//a/text()[contains(., "Issuer profile")]/../@href')
        # #print(issueTab[0])
        # if issueTab:
        #     number = re.findall('ctl00\$body\$IFTabsControlDetails\$lb\d', issueTab[0])
        #     if number:
        #         number = str(number[0][-1])
        # data = self.getHiddenValuesASP()
        # data['ctl00$MasterScriptManager'] = f'ctl00$body$IFTabsControlDetails$ctl00|ctl00$body$IFTabsControlDetails$lb{number}'
        # data['__EVENTTARGET'] = f'ctl00$body$IFTabsControlDetails$lb{number}'
        # data['__ASYNCPOST'] = 'true'
        # data['ctl00$body$ctl02$NewsBySymbolControl$chOutVolatility'] = 'on'
        # data['ctl00$body$ctl02$NewsBySymbolControl$chOutInsiders'] = 'on'
        # data['gv_length'] = '10'
        # data['autocomplete-form-mob'] = ''
        # self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        # self.get_working_tree_api(link_name, 'tree', method='POST', data=data)
        # #self.check_tree()
        #
        #
        #
        #
        # self.get_address('//td//text()[contains(., "Address")]/../following-sibling::td//text()', zipPattern='\d\d\d\d\d')
        #
        #
        #
        #
        #
        #
        # self.fill_identifiers(
        #     xpathLegalEntityIdentifier='//td//text()[contains(., "LEI Code")]/../following-sibling::td//text()',
        #     xpathOtherCompanyId='//td//text()[contains(., "Fiscal / Unique Code")]/../following-sibling::td//text()'
        #     )
        # try:
        #     self.overview['bst:registrationId'] = self.overview['identifiers']['other_company_id_number']
        # except:
        #     pass
        #
        #






        #print(self.overview)


        #exit()
        # self.fillField('bst:aka', xpath='//div[@class="AliasList"]//div/text()')
        # self.get_address(xpath='//div[@class="MasterBorder"]//div[2]//div/text()', zipPattern='\d\d\d\d\d+')
        # if self.overview['mdaas:RegisteredAddress']['fullAddress']:
        #     try:
        #         self.overview['registeredIn'] = self.overview['mdaas:RegisteredAddress']['fullAddress'].split(',')[-2].split(' ')[1]
        #     except:
        #         pass
        #
        # self.fill_business_classifier(xpathCodes='//table/@class[contains(., "matrix")]/..//tr/td[2]/text()', xpathDesc='//table/@class[contains(., "matrix")]/..//tr/td[1]/text()')
        #
        #
        # self.overview['regulator_name'] = 'Idaho department of Insurance'
        # self.overview['regulator_url'] = self.base_url
        # self.overview['RegulationStatus'] = 'Authorised'
        #
        # self.fillField('RegulationStatusEffectiveDate',
        #                xpath='//td//text()[contains(., "Date Effective")]/../../following-sibling::td//text()',
        #                reformatDate='%m/%d/%Y')
        #
        # self.fillField('regExpiryDate',
        #                xpath='//td//text()[contains(., "Date Expire")]/../../following-sibling::td//text()',
        #                reformatDate='%m/%d/%Y')
        # self.fill_identifiers(xpathOtherCompanyId='//td//text()[contains(., "NAIC Code")]/../../following-sibling::td//text()')
        #
        #
        #
        #
        # try:
        #     if self.overview['bst:businessClassifier']:
        #         self.overview['Service'] = {
        #             'areaServed': '',
        #             'serviceType': ', '.join(i['description'] for i in self.overview['bst:businessClassifier'])
        #         }
        # except:
        #     pass
        #
        # self.get_working_tree_api('https://doi.idaho.gov/agency-contact/director/', 'tree')
        # self.fillRegulatorAddress(xpath='//div/@class[contains(., "footer-widget")]/..//p[1]/strong/text()[contains(., "Main Office")]/../..//text()')
        # exit()

        # self.fillField('logo', xpath='')


        #
        #


        # self.fill_business_classifier(xpathDesc='//categories//span/text()')
        #
        # self.fillField('bst:description', xpath='//h2/@class[contains(., "section-headline")]/../following-sibling::div[1]//text()')
        #
        #
        #
        #
        # self.fill_identifiers(xpathTradeRegistry='//div/text()[contains(., "Handelsregister")]/../following-sibling::div[1]/span/text()')
        #
        # self.overview['@source-id'] = self.NICK_NAME
        # self.fillRatingSummary(xpathRatingGroup='//div[@class="score-summary"]//div[@class="grade-name"]/text()',
        #                 xpathRatings='//h3/@class[contains(., "yearly-rating-count")]/../text()')
        # self.fillAgregateRating(xpathReview='//div/@class[contains(., "total-rating-count")]/../text()',
        #                         xpathRatingValue='//div[@class="score-info"]//span/text()')
        # self.fillReviews(xpathRatingValue='//rating-stars/span/@class[contains(., "active")]',
        #                  xpathReviews='//review',
        #                  xpathDate='//loading-line[2]/div/span/span/text()',
        #                  xpathDesc='//loading-line[1]/div/div/text()')



        #print(self.overview)
        #exit()




        # self.fillField('bst:aka',
        #                xpath='//div[@class="sectionHeader"]/text()[contains(., "Contact Information")]/../following-sibling::div[1]//tr[1]/td[2]/text()')
        #
        # self.get_address(
        #     xpath='//div[@class="sectionHeader"]/text()[contains(., "Address")]/../following-sibling::div[1]//text()',
        #     zipPattern='\d\d\d\d\d+')

        # # self.fillField('bst:description',
        #                xpath='//div[@class="sectionHeader"]/text()[contains(., "Purpose")]/../following-sibling::div[1]/text()')
        #
        # self.fillField('identifiers',
        #                xpath='//div[@class="sectionHeader"]/text()[contains(., "Filing Information")]/../following-sibling::div[1]//td/text()[contains(., "Filing Number")]/../following-sibling::td/text()')
        # self.fillField('bst:registrationId',
        #                xpath='//div[@class="sectionHeader"]/text()[contains(., "Filing Information")]/../following-sibling::div[1]//td/text()[contains(., "Filing Number")]/../following-sibling::td/text()')
        # if self.overview['bst:registrationId']:
        #     self.overview['bst:registrationId'] = self.overview['bst:registrationId']
        # self.overview['regulator_name'] = 'Michal watson - Mississippi Secretary of State'
        # self.overview['regulatorAddress'] = {
        #     'fullAddress': 'New Capitol Room 105 Jackson, Mississippi 39201, United state',
        #     'city': 'Jackson',
        #     'country': 'United States'
        # }
        # self.overview['regulator_url'] = 'https://www.sos.ms.gov/contact-us/capitol-office'
        # self.overview['RegulationStatus'] = 'Active'
        # self.overview[
        #     'bst:registryURI'] = 'https://charities.sos.ms.gov/online/portal/ch/page/charities-search/Portal.aspx#'


        # self.overview['@source-id'] = self.NICK_NAME
        # print(self.overview)
        # exit()

        # print(self.overview)
        # exit()
        # # self.overview['bst:sourceLinks'] = link_name
        #
        # self.fillField('vcard:organization-tradename', key='Trade Name(s)')

        # self.fillField('previous_names', key='Former Name(s)')
        # self.fillField('lei:legalForm', key='Business Type')

        #
        # self.fillField('Service', key='Business In')
        # self.fillField('agent', key='Chief Agent')
        # self.fillField('previous_names', key='Former Name(s)')
        # self.fillField('regExpiryDate', key='Expiry Date', reformatDate='%d-%b-%Y')
        # self.overview[
        #     'bst:registryURI'] = f'https://www.princeedwardisland.ca/en/feature/pei-business-corporate-registry-original#/service/LegacyBusiness/LegacyBusinessView;e=LegacyBusinessView;business_number={self.api["Registration Number"]}'
        # self.overview['@source-id'] = self.NICK_NAME

        # print(self.overview)
        # exit()
        # self.fillField('lei:legalForm', '//div/text()[contains(., "Legal form")]/../following-sibling::div//text()')
        # self.fillField('identifiers', '//div/text()[contains(., "Registry code")]/../following-sibling::div//text()')
        # self.fillField('map', '//div/text()[contains(., "Address")]/../following-sibling::div/a/@href')
        # self.fillField('incorporationDate', '//div/text()[contains(., "Registered")]/../following-sibling::div/text()')

        # self.fillField('bst:businessClassifier', '//div/text()[contains(., "EMTAK code")]/../following-sibling::div/text()')
        # self.get_business_class('//div/text()[contains(., "EMTAK code")]/../following-sibling::div/text()',
        #                         '//div/text()[contains(., "Area of activity")]/../following-sibling::div/text()',
        #                         '//div/text()[contains(., "EMTAK code")]/../following-sibling::div/text()')
        #
        # self.get_address('//div/text()[contains(., "Address")]/../following-sibling::div/text()',
        #                  zipPattern='\d{5}')
        #
        # self.overview['sourceDate'] = datetime.datetime.today().strftime('%Y-%m-%d')



        # print(self.overview)
        return self.overview

    def get_officership(self, link_name):
        off = []

        link_name = link_name.replace("'",'"').replace("None", '"None"')
        self.api =json.loads(link_name)



        try:
            for d in self.api['BoardOfDirectors'].split(', '):
                off.append(
                            {'name': d,
                                        'type': 'individual',
                                        'officer_role': 'director',
                                        'status': 'Active',
                                        'occupation': 'director',
                                        'information_source': self.base_url,
                                        'information_provider': 'The Nigerian Stock Exchange'})
        except:
            pass

        try:
            for d in [self.api['CompanySecretary']]:
                off.append(
                            {'name': d,
                                        'type': 'individual',
                                        'officer_role': 'Secretary',
                                        'status': 'Active',
                                        'occupation': 'Secretary',
                                        'information_source': self.base_url,
                                        'information_provider': 'The Nigerian Stock Exchange'})
        except:
            pass




        # self.get_working_tree_api(link_name, 'tree')

        # issueTab = self.get_by_xpath('//a/text()[contains(., "Issuer profile")]/../@href')
        # # print(issueTab[0])
        # if issueTab:
        #     number = re.findall('ctl00\$body\$IFTabsControlDetails\$lb\d', issueTab[0])
        #     if number:
        #         number = str(number[0][-1])
        # data = self.getHiddenValuesASP()
        # data[
        #     'ctl00$MasterScriptManager'] = f'ctl00$body$IFTabsControlDetails$ctl00|ctl00$body$IFTabsControlDetails$lb{number}'
        # data['__EVENTTARGET'] = f'ctl00$body$IFTabsControlDetails$lb{number}'
        # data['__ASYNCPOST'] = 'true'
        # data['ctl00$body$ctl02$NewsBySymbolControl$chOutVolatility'] = 'on'
        # data['ctl00$body$ctl02$NewsBySymbolControl$chOutInsiders'] = 'on'
        # data['gv_length'] = '10'
        # data['autocomplete-form-mob'] = ''
        # self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        # self.get_working_tree_api(link_name, 'tree', method='POST', data=data)
        #
        # try:
        #     t1 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[2]/td/text()')[0]
        #     n1 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[3]/td/text()')[0]
        #     t2 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[6]/td/text()')[0]
        #     n2 = self.tree.xpath('//table[@id="ctl00_body_ctl02_CompanyProfile_dvIssCA"]//tr/td/table//tr[7]/td/text()')[0]
        #     off.append(
        #             {'name': n1,
        #                         'type': 'individual',
        #                         'officer_role': t1,
        #                         'status': 'Active',
        #                         'occupation': t1,
        #                         'information_source': self.base_url,
        #                         'information_provider': 'Bucharest Stock Exchange'}
        #         )
        #     if n1 != n2:
        #         off.append(
        #             {'name': n2,
        #              'type': 'individual',
        #              'officer_role': t2,
        #              'status': 'Active',
        #              'occupation': t2,
        #              'information_source': self.base_url,
        #              'information_provider': 'Bucharest Stock Exchange'}
        #         )
        # except:
        #     pass




        # exit()
        #
        #
        #
        #
        # officership_prod_links = self.get_by_xpath('//div[@id="agentTable"]//td/a/@href')
        # officership_insur_links = self.get_by_xpath('//div[@id="companyTable"]//td/a/@href')
        # officership_prod_links = [self.base_url+i for i in officership_prod_links]
        # officership_insur_links = [self.base_url+i for i in officership_insur_links]
        #
        # for i in officership_prod_links[:-1]:
        #     officer = self.getOfficerFromPage(i, 'individual')
        #     if officer:
        #         off.append(officer)
        # for i in officership_insur_links[:-1]:
        #     officer = self.getOfficerFromPage(i, 'company')
        #     if officer:
        #         off.append(officer)




        # names = self.get_by_api('Officer(s)')
        # if '\n' in names:
        #     names = names.split('\n')
        # # roles = self.get_by_xpath(
        # #     '//div/text()[contains(., "Right of representation")]/../following-sibling::div//tr/td[3]/text()')
        #
        # off = []
        # names = [names] if type(names) == str else names
        # roles = []
        # for name in names:
        #     roles.append(name.split(' - ')[-1])
        # names = [i.split(' - ')[0] for i in names]
        #
        # # roles = [roles] if type(roles) == str else roles
        # for n, r in zip(names, roles):
        #     home = {'name': n,
        #             'type': 'individual',
        #             'officer_role': r,
        #             'status': 'Active',
        #             'occupation': r,
        #             'information_source': self.base_url,
        #             'information_provider': 'Prince Edward Island Corporate Registry'}
        #     off.append(home)
        return off

    def get_documents(self, link_name):
        docs = []

        link_name = link_name.replace("'", '"').replace("None", '"None"')
        self.api = json.loads(link_name)

        comp = self.api['InternationSecIN']

        url = f"https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('XFinancial_News')/items/?$select=URL,Modified,InternationSecIN,Type_of_Submission&$orderby=Modified%20desc&$filter=InternationSecIN%20eq%20%27{self.api['InternationSecIN']}%27%20and%20(Type_of_Submission%20eq%20%27Financial%20Statements%27%20or%20Type_of_Submission%20eq%20%27EarningForcast%27)"


        self.header['Accept'] = 'application/json;odata=verbose'
        self.get_working_tree_api(url, 'api')
        self.api = self.api['d']['results']

        for doc in self.api[:1]:
            temp = {
                'url': doc['URL']['Url'],
                'description': 'financial statements',
                'date': doc['Modified'].split('T')[0]
            }
            docs.append(temp)


        url = f"https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('XFinancial_News')/items/?$select=URL,Modified,InternationSecIN,Type_of_Submission&$orderby=Modified%20desc&$filter=InternationSecIN%20eq%20%27{comp}%27%20and%20(Type_of_Submission%20eq%20%27Corporate%20Actions%27%20or%20Type_of_Submission%20eq%20%27Corporate%20Disclosures%27%20or%20substringof(%27Meeting%27%20,Type_of_Submission))"
        self.header['Accept'] = 'application/json;odata=verbose'
        self.get_working_tree_api(url, 'api')

        self.api = self.api['d']['results']

        for doc in self.api[:10]:
            temp = {
                'url': doc['URL']['Url'],
                'description': 'corporate disclosure',
                'date': doc['Modified'].split('T')[0]
            }
            docs.append(temp)

        url = f"https://doclib.ngxgroup.com/_api/Web/Lists/GetByTitle('XFinancial_News')/items/?$select=URL,Modified,InternationSecIN,Type_of_Submission&$orderby=Modified%20desc&$filter=(InternationSecIN%20eq%20%27{comp}%27%20and%20(Type_of_Submission%20eq%20%27DirectorsDealings%27%20or%20Type_of_Submission%20eq%20%27Directors%20Dealings%27))"
        self.header['Accept'] = 'application/json;odata=verbose'
        self.get_working_tree_api(url, 'api')

        self.api = self.api['d']['results']

        for doc in self.api[:10]:
            temp = {
                'url': doc['URL']['Url'],
                'description': 'directors dealing',
                'date': doc['Modified'].split('T')[0]
            }
            docs.append(temp)



        #
        # issueTab = self.get_by_xpath('//a/text()[contains(., "Issuer profile")]/../@href')
        # # print(issueTab[0])
        # if issueTab:
        #     number = re.findall('ctl00\$body\$IFTabsControlDetails\$lb\d', issueTab[0])
        #     if number:
        #         number = str(number[0][-1])
        # data = self.getHiddenValuesASP()
        # data[
        #     'ctl00$MasterScriptManager'] = f'ctl00$body$IFTabsControlDetails$ctl00|ctl00$body$IFTabsControlDetails$lb{number}'
        # data['__EVENTTARGET'] = f'ctl00$body$IFTabsControlDetails$lb{number}'
        # data['__ASYNCPOST'] = 'true'
        # data['ctl00$body$ctl02$NewsBySymbolControl$chOutVolatility'] = 'on'
        # data['ctl00$body$ctl02$NewsBySymbolControl$chOutInsiders'] = 'on'
        # data['gv_length'] = '10'
        # data['autocomplete-form-mob'] = ''
        # self.header['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        # self.get_working_tree_api(link_name, 'tree', method='POST', data=data)
        #
        #
        # texts = self.tree.xpath('//div/text()[contains(., "Issuer documents")]/following-sibling::div[1]/div//td//text()')
        # texts = [i.strip() for i in texts]
        # texts = [i for i in texts if i]
        #
        # links = self.tree.xpath('//div/text()[contains(., "Issuer documents")]/following-sibling::div[1]/div//td/a/@href')
        # links = [self.base_url+i for i in links]





        return docs

    def get_financial_information(self, link_name):
        # self.get_working_tree_api(link_name, 'tree')

        link_name = link_name.replace("'", '"').replace("None", '"None"')
        self.api = json.loads(link_name)
        print(self.api)


        fin = {}
        temp = {
            'stock_id': ''
        }

        try:
            temp['stock_name'] = ''
        except:
            pass

        curr = {
            'data_date': datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
        }
        #open = self.get_by_xpath('//td//text()[contains(., "Open price")]/../following-sibling::td//text()')
        if open:
            curr['open_price'] = str(self.api['OpenPrice'])

        # min = self.get_by_xpath('//td//text()[contains(., "Low price")]/../following-sibling::td//text()')
        # max = self.get_by_xpath('//td//text()[contains(., "High price")]/../following-sibling::td//text()')
        min = self.api['DaysLow']
        max = self.api['DaysHigh']

        if min and max:
            curr['day_range'] = f'{min}-{max}'

        #vol = self.get_by_xpath('//td//text()[contains(., "Total no. of shares")]/../following-sibling::td//text()')
        vol = self.api['Volume']
        if vol:
            curr['volume'] = str(vol)

        #prClose= self.get_by_xpath('//td//text()[contains(., "Last price")]/../following-sibling::td//text()')
        prClose = self.api['PrevClose']
        if prClose:
            curr['prev_close_price'] = str(prClose)

        # cap = self.get_by_xpath('//td//text()[contains(., "Market cap")]/../following-sibling::td//text()')
        cap = self.api['MarketCap']
        if cap:
            curr['market_capitalization'] = str(cap)

        curr['exchange_currency'] = 'naira'

        # min52 = self.get_by_xpath('//td//text()[contains(., "52 weeks low")]/../following-sibling::td//text()')
        # max52 = self.get_by_xpath('//td//text()[contains(., "52 weeks high")]/../following-sibling::td//text()')
        min52 = self.api['LOW52WK_PRICE']
        max52 = self.api['HIGH52WK_PRICE']
        if min52 and max52:
            curr['52_week_range'] = f'{min52}-{max52}'





        temp['current'] = curr
        fin['stocks_information'] = [temp]


        #summ = self.get_by_xpath('//div/text()[contains(., "Capital")]/../following-sibling::div//text()')

        # if summ:
        #     summ = re.findall('\d+', summ[0])
        #     if summ:
        fin['Summary_Financial_data'] = [{
            'summary': {
                'currency': 'naira',
                'balance_sheet': {
                    'market_capitalization': str(self.api['MarketCap'])
                }
            }
        }]
        self.get_working_tree_api(f'https://ngxgroup.com/exchange/data/company-profile/?isin={self.api["InternationSecIN"]}&directory=companydirectory','tree')

        res = []
        dates = self.tree.xpath('//h3/text()[contains(., "Last 7 Days Trades")]/../../following-sibling::div[1]//tr/td[1]/text()')[:-1]
        prices =self.tree.xpath('//h3/text()[contains(., "Last 7 Days Trades")]/../../following-sibling::div[1]//tr/td[2]/text()')[:-1]
        volumes = self.tree.xpath('//h3/text()[contains(., "Last 7 Days Trades")]/../../following-sibling::div[1]//tr/td[3]/text()')[:-1]
        prPrices = prices[1:]

        for d,p,v, pr in zip(dates, prices, volumes, prPrices):
            res.append(
                {
                    'data_date': datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d'),
                    'open_price': pr,
                    'close_price': p,
                    'volume': v,
                    'day_range': f'{pr}-{p}',
                }
            )
        fin['stocks_information'].append({'historical_prices': res})


        return fin




    # def get_shareholders(self, link_name):
    #
    #     edd = {}
    #     shareholders = {}
    #     sholdersl1 = {}
    #
    #     company = self.get_overview(link_name)
    #     company_name_hash = hashlib.md5(company['vcard:organization-name'].encode('utf-8')).hexdigest()
    #     self.get_working_tree_api(link_name, 'api')
    #     # print(self.api)
    #
    #     try:
    #         names = self.get_by_api('Shareholder(s)')
    #         if len(re.findall('\d+', names)) > 0:
    #             return edd, sholdersl1
    #         if '\n' in names:
    #             names = names.split('\n')
    #
    #         holders = [names] if type(names) == str else names
    #
    #         for i in range(len(holders)):
    #             holder_name_hash = hashlib.md5(holders[i].encode('utf-8')).hexdigest()
    #             shareholders[holder_name_hash] = {
    #                 "natureOfControl": "SHH",
    #                 "source": 'Prince Edward Island Corporate Registry',
    #             }
    #             basic_in = {
    #                 "vcard:organization-name": holders[i],
    #                 'isDomiciledIn': 'CA'
    #             }
    #             sholdersl1[holder_name_hash] = {
    #                 "basic": basic_in,
    #                 "shareholders": {}
    #             }
    #     except:
    #         pass
    #
    #     edd[company_name_hash] = {
    #         "basic": company,
    #         "entity_type": "C",
    #         "shareholders": shareholders
    #     }
    #     # print(sholdersl1)
    #     return edd, sholdersl1

    # def get_financial_information(self, link):
    #     data = {
    #         "searchType": "Charity_Services_IFSSearchResults",
    #         "entityName": link,
    #         "fileNumber": "",
    #         "filingClassId": "00000000-0000-0000-0000-000000000000"
    #     }
    #     url = 'https://charities.sos.ms.gov/online/Services/Common/IFSServices.asmx/ExecuteSearch'
    #     self.get_working_tree_api(url, 'api', method='POST', data=data)
    #     g = self.api['d']
    #     d = json.loads(g)
    #     self.api = d['Table'][0]
    #     url = f'https://charities.sos.ms.gov/online/portal/ch/page/charities-search/~/ViewXSLTFileByName.aspx?providerName=CH_EntityBasedFilingDetails&FilingId={self.api["FilingId"]}'
    #     self.get_working_tree_api(url, 'tree')
    #
    #     period = self.get_by_xpath(
    #         '//div[@class="sectionHeader"]/text()[contains(., "Financial Information")]/../following-sibling::div/div/text()')
    #     revenue = self.get_by_xpath(
    #         '//div[@class="sectionHeader"]/text()[contains(., "Financial Information")]/../following-sibling::div/div//td/text()[contains(., "Total Revenue")]/../following-sibling::td/text()')
    #     temp = {}
    #     if period and revenue:
    #         period = [self.reformat_date(i.split(': ')[-1], '%m/%d/%Y') for i in period]
    #         revenue = [i[2:] for i in revenue]
    #         tempList = []
    #         for p, r in zip(period, revenue):
    #             tempList.append({
    #                 'period': p,
    #                 'revenue': r
    #             })
    #
    #         temp['Summary_Financial_data'] = [{
    #             'source': 'Michael Watson Secretory of state',
    #             'summary': {
    #                 'currency': 'USD',
    #                 'income_statement': tempList[0]
    #             }
    #         }]
    #     # print(temp)
    #     return temp
