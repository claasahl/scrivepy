import enum
from dateutil import parser as dateparser

import type_value_unifier as tvu
from scrivepy import _object, _signatory, _exceptions


scrive_property = _object.scrive_property


class SignatorySet(tvu.TypeValueUnifier):

    TYPES = (set,)

    def validate(self, value):
        for elem in value:
            if not isinstance(elem, _signatory.Signatory):
                self.error(u'set of Signatory objects')


class DocumentStatus(unicode, enum.Enum):
    preparation = u'Preparation'
    pending = u'Pending'
    closed = u'Closed'
    canceled = u'Canceled'
    timedout = u'Timedout'
    rejected = u'Rejected'
    error = u'DocumentError'


MaybeUnicode = tvu.nullable(tvu.instance(unicode))


class Language(unicode, enum.Enum):
    english = u'en'
    swedish = u'sv'
    german = u'de'
    french = u'fr'
    italian = u'it'
    spanish = u'es'
    portuguese = u'pt'
    dutch = u'nl'
    danish = u'da'
    norwegian = u'no'
    greek = u'el'
    finnish = u'fi'


class Document(_object.ScriveObject):

    @tvu.validate_and_unify(title=tvu.instance(unicode),
                            number_of_days_to_sign=tvu.bounded_int(1, 90),
                            number_of_days_to_remind=
                            tvu.nullable(tvu.PositiveInt),
                            is_template=tvu.instance(bool),
                            show_header=tvu.instance(bool),
                            show_pdf_download=tvu.instance(bool),
                            show_reject_option=tvu.instance(bool),
                            show_footer=tvu.instance(bool),
                            invitation_message=MaybeUnicode,
                            confirmation_message=MaybeUnicode,
                            api_callback_url=MaybeUnicode,
                            language=tvu.instance(Language, enum=True),
                            tags=tvu.UnicodeDict,
                            signatories=SignatorySet)
    def __init__(self, title=u'', number_of_days_to_sign=14,
                 number_of_days_to_remind=None,
                 show_header=True, show_pdf_download=True,
                 show_reject_option=True, show_footer=True,
                 invitation_message=None, confirmation_message=None,
                 api_callback_url=None, language=Language.swedish,
                 tags={}, is_template=False, signatories=set()):
        super(Document, self).__init__()
        self._id = None
        self._title = title
        self._number_of_days_to_sign = number_of_days_to_sign
        self._number_of_days_to_remind = number_of_days_to_remind
        self._status = None
        self._modification_time = None
        self._creation_time = None
        self._signing_deadline = None
        self._autoremind_time = None
        self._current_sign_order = None
        self._is_template = is_template
        self._show_header = show_header
        self._show_pdf_download = show_pdf_download
        self._show_reject_option = show_reject_option
        self._show_footer = show_footer
        self.invitation_message = invitation_message  # setter has better logic
        self.confirmation_message = \
            confirmation_message  # setter has better logic
        self._api_callback_url = api_callback_url
        self._language = language
        self._tags = tags.copy()
        self._signatories = set(signatories)

    @classmethod
    def _from_json_obj(cls, json):
        try:
            signatories = \
                set([_signatory.Signatory._from_json_obj(signatory_json)
                     for signatory_json in json[u'signatories']])
            lang_code = json[u'lang']
            if lang_code == u'gb':
                lang_code = u'en'
            document = Document(title=json[u'title'],
                                number_of_days_to_sign=json[u'daystosign'],
                                number_of_days_to_remind=json[u'daystoremind'],
                                is_template=json[u'template'],
                                show_header=json[u'showheader'],
                                show_pdf_download=json[u'showpdfdownload'],
                                show_reject_option=json[u'showrejectoption'],
                                show_footer=json[u'showfooter'],
                                invitation_message=json[u'invitationmessage'],
                                confirmation_message=
                                json[u'confirmationmessage'],
                                api_callback_url=json[u'apicallbackurl'],
                                language=Language(lang_code),
                                tags={elem[u'name']: elem[u'value']
                                      for elem in json[u'tags']},
                                signatories=signatories)
            document._id = json[u'id']
            if json[u'time'] is not None:
                document._modification_time = dateparser.parse(json[u'time'])
            if json[u'ctime'] is not None:
                document._creation_time = dateparser.parse(json[u'ctime'])
            if json[u'timeouttime'] is not None:
                document._signing_deadline = \
                    dateparser.parse(json[u'timeouttime'])
            if json[u'autoremindtime'] is not None:
                document._autoremind_time = \
                    dateparser.parse(json[u'autoremindtime'])
            document._status = DocumentStatus(json[u'status'])
            document._current_sign_order = json[u'signorder']
            return document
        except (KeyError, TypeError, ValueError) as e:
            raise _exceptions.InvalidResponse(e)

    def _set_invalid(self):
        # invalidate signatories first, before getter stops working
        for signatory in self.signatories:
            signatory._set_invalid()
        super(Document, self)._set_invalid()

    def _set_read_only(self):
        super(Document, self)._set_read_only()
        for signatory in self.signatories:
            signatory._set_read_only()

    def _to_json_obj(self):
        return {u'title': self.title,
                u'daystosign': self.number_of_days_to_sign,
                u'daystoremind': self.number_of_days_to_remind,
                u'template': self.is_template,
                u'showheader': self.show_header,
                u'showpdfdownload': self.show_pdf_download,
                u'showrejectoption': self.show_reject_option,
                u'showfooter': self.show_footer,
                u'invitationmessage': self.invitation_message or u'',
                u'confirmationmessage': self.confirmation_message or u'',
                u'apicallbackurl': self.api_callback_url,
                u'lang': self.language.value,
                u'tags': [{u'name': key, u'value': val}
                          for key, val in self.tags.items()],
                u'signatories': list(self.signatories)}

    @scrive_property
    def signatories(self):
        return iter(self._signatories)

    @signatories.setter
    @tvu.validate_and_unify(signatories=SignatorySet)
    def signatories(self, signatories):
        self._signatories = set(signatories)

    @scrive_property
    def id(self):
        return self._id

    @scrive_property
    def title(self):
        return self._title

    @title.setter
    @tvu.validate_and_unify(title=tvu.instance(unicode))
    def title(self, title):
        self._title = title

    @scrive_property
    def number_of_days_to_sign(self):
        return self._number_of_days_to_sign

    @number_of_days_to_sign.setter
    @tvu.validate_and_unify(number_of_days_to_sign=tvu.bounded_int(1, 90))
    def number_of_days_to_sign(self, number_of_days_to_sign):
        self._number_of_days_to_sign = number_of_days_to_sign

    @scrive_property
    def status(self):
        return self._status

    @scrive_property
    def modification_time(self):
        return self._modification_time

    @scrive_property
    def creation_time(self):
        return self._creation_time

    @scrive_property
    def signing_deadline(self):
        return self._signing_deadline

    @scrive_property
    def autoremind_time(self):
        return self._autoremind_time

    @scrive_property
    def current_sign_order(self):
        return self._current_sign_order

    @scrive_property
    def authentication_method(self):
        signatories = list(self.signatories)
        if not signatories:
            return u'mixed'

        # at least 1 signatory
        first_signatory = signatories.pop(0)
        result = first_signatory.authentication_method
        for signatory in signatories:
            if signatory.authentication_method != result:
                # signatories use various auth methods
                return u'mixed'
        # all signatories have the same auth method
        return result.value

    @scrive_property
    def invitation_delivery_method(self):
        signatories = list(self.signatories)
        if not signatories:
            return u'mixed'

        # at least 1 signatory
        first_signatory = signatories.pop(0)
        result = first_signatory.invitation_delivery_method
        for signatory in signatories:
            if signatory.invitation_delivery_method != result:
                # signatories use various invitation delivery methods
                return u'mixed'
        # all signatories have the same invitation delivery method
        return result.value

    @scrive_property
    def is_template(self):
        return self._is_template

    @is_template.setter
    @tvu.validate_and_unify(is_template=tvu.instance(bool))
    def is_template(self, is_template):
        self._is_template = is_template

    @scrive_property
    def number_of_days_to_remind(self):
        return self._number_of_days_to_remind

    @number_of_days_to_remind.setter
    @tvu.validate_and_unify(
        number_of_days_to_remind=tvu.nullable(tvu.PositiveInt))
    def number_of_days_to_remind(self, number_of_days_to_remind):
        self._number_of_days_to_remind = number_of_days_to_remind

    @scrive_property
    def show_header(self):
        return self._show_header

    @show_header.setter
    @tvu.validate_and_unify(show_header=tvu.instance(bool))
    def show_header(self, show_header):
        self._show_header = show_header

    @scrive_property
    def show_pdf_download(self):
        return self._show_pdf_download

    @show_pdf_download.setter
    @tvu.validate_and_unify(show_pdf_download=tvu.instance(bool))
    def show_pdf_download(self, show_pdf_download):
        self._show_pdf_download = show_pdf_download

    @scrive_property
    def show_reject_option(self):
        return self._show_reject_option

    @show_reject_option.setter
    @tvu.validate_and_unify(show_reject_option=tvu.instance(bool))
    def show_reject_option(self, show_reject_option):
        self._show_reject_option = show_reject_option

    @scrive_property
    def show_footer(self):
        return self._show_footer

    @show_footer.setter
    @tvu.validate_and_unify(show_footer=tvu.instance(bool))
    def show_footer(self, show_footer):
        self._show_footer = show_footer

    @scrive_property
    def invitation_message(self):
        return self._invitation_message

    @invitation_message.setter
    @tvu.validate_and_unify(invitation_message=MaybeUnicode)
    def invitation_message(self, invitation_message):
        if invitation_message is not None and invitation_message.isspace()\
           or invitation_message == u'':
            invitation_message = None
        self._invitation_message = invitation_message

    @scrive_property
    def confirmation_message(self):
        return self._confirmation_message

    @confirmation_message.setter
    @tvu.validate_and_unify(confirmation_message=MaybeUnicode)
    def confirmation_message(self, confirmation_message):
        if confirmation_message is not None and confirmation_message.isspace()\
           or confirmation_message == u'':
            confirmation_message = None
        self._confirmation_message = confirmation_message

    @scrive_property
    def api_callback_url(self):
        return self._api_callback_url

    @api_callback_url.setter
    @tvu.validate_and_unify(api_callback_url=MaybeUnicode)
    def api_callback_url(self, api_callback_url):
        self._api_callback_url = api_callback_url

    @scrive_property
    def language(self):
        return self._language

    @language.setter
    @tvu.validate_and_unify(language=tvu.instance(Language, enum=True))
    def language(self, language):
        self._language = language

    @scrive_property
    def tags(self):
        return self._tags

    @tags.setter
    @tvu.validate_and_unify(tags=tvu.UnicodeDict)
    def tags(self, tags):
        self._tags = tags



# documentJSONV1 :: (MonadDB m, MonadThrow m, Log.MonadLog m, MonadIO m, AWS.AmazonMonad m) => (Maybe User) -> Bool -> Bool -> Bool ->  Maybe SignatoryLink -> Document -> m JSValue
# documentJSONV1 muser includeEvidenceAttachments forapi forauthor msl doc = do
#     file <- documentfileM doc
#     sealedfile <- documentsealedfileM doc
#     authorattachmentfiles <- mapM (dbQuery . GetFileByFileID . authorattachmentfile) (documentauthorattachments doc)
#     evidenceattachments <- if includeEvidenceAttachments then EvidenceAttachments.fetch doc else return []
#     runJSONGenT $ do
#       J.value "file" $ fmap fileJSON file
#       J.value "sealedfile" $ fmap fileJSON sealedfile
#       J.value "authorattachments" $ map fileJSON authorattachmentfiles
#       J.objects "evidenceattachments" $ for evidenceattachments $ \a -> do
#         J.value "name"     $ BSC.unpack $ EvidenceAttachments.name a
#         J.value "mimetype" $ BSC.unpack <$> EvidenceAttachments.mimetype a
#         J.value "downloadLink" $ show $ LinkEvidenceAttachment (documentid doc) (EvidenceAttachments.name a)
#       J.value "saved" $ not (documentunsaveddraft doc)
#       J.value "deleted" $ fromMaybe False $ documentDeletedForUser doc <$> userid <$> muser
#       J.value "reallydeleted" $ fromMaybe False $ documentReallyDeletedForUser doc <$> userid <$>  muser
#       when (isJust muser) $
#         J.value "canperformsigning" $ userCanPerformSigningAction (userid $ fromJust muser) doc
#       J.value "objectversion" $ documentobjectversion doc
#       J.value "process" $ "Contract"
#       J.value "isviewedbyauthor" $ isSigLinkFor muser (getAuthorSigLink doc)
#       when (not $ forapi) $ do
#         J.value "canberestarted" $ isAuthor msl && ((documentstatus doc) `elem` [Canceled, Timedout, Rejected])
#         J.value "canbeprolonged" $ isAuthor msl && ((documentstatus doc) `elem` [Timedout])
#         J.value "canbecanceled" $ (isAuthor msl || fromMaybe False (useriscompanyadmin <$> muser)) && documentstatus doc == Pending
#         J.value "canseeallattachments" $ isAuthor msl || fromMaybe False (useriscompanyadmin <$> muser)
#       J.value "accesstoken" $ show (documentmagichash doc)
#       J.value "timezone" $ toString $ documenttimezonename doc

# instance FromJSValueWithUpdate Document where
#     fromJSValueWithUpdate mdoc = do
#         mtimezone <- fromJSValueField "timezone"
#         saved <- fromJSValueField "saved"
#         authorattachments <- fromJSValueFieldCustom "authorattachments" $ fromJSValueCustomMany $ fmap (join . (fmap maybeRead)) $ (fromJSValueField "id")
#         return $ Just defaultValue {
#             documentauthorattachments = updateWithDefaultAndField [] documentauthorattachments (fmap AuthorAttachment <$> authorattachments),
#             documentunsaveddraft = updateWithDefaultAndField False documentunsaveddraft (fmap not saved),
#             documenttimezonename = updateWithDefaultAndField defaultTimeZoneName documenttimezonename (unsafeTimeZoneName <$> mtimezone)
#           }
#       where
#        updateWithDefaultAndField :: a -> (Document -> a) -> Maybe a -> a
#        updateWithDefaultAndField df uf mv = fromMaybe df (mv `mplus` (fmap uf mdoc))
