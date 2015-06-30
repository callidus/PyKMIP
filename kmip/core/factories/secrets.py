# Copyright (c) 2014 The Johns Hopkins University/Applied Physics Laboratory
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from kmip.core.factories.keys import KeyFactory

from kmip.core.attributes import CryptographicAlgorithm
from kmip.core.attributes import CryptographicLength
from kmip.core.attributes import UniqueIdentifier

from kmip.core.enums import ObjectType
from kmip.core.errors import ErrorStrings
from kmip.core.misc import KeyFormatType

from kmip.core.objects import Attribute
from kmip.core.objects import KeyBlock
from kmip.core.objects import KeyMaterial
from kmip.core.objects import KeyWrappingData
from kmip.core.objects import WrappingMethod
from kmip.core.objects import EncodingOption
from kmip.core.objects import EncryptionKeyInformation
from kmip.core.objects import MACSignatureKeyInformation
from kmip.core.objects import KeyValue

from kmip.core.secrets import Certificate
from kmip.core.secrets import OpaqueObject
from kmip.core.secrets import PrivateKey
from kmip.core.secrets import PublicKey
from kmip.core.secrets import SecretData
from kmip.core.secrets import SymmetricKey
from kmip.core.secrets import Template

from kmip.core import utils


class SecretFactory(object):

    def __init__(self):
        self.key_factory = KeyFactory()

        self.base_error = ErrorStrings.BAD_EXP_RECV
        self.template_input = self.base_error.format('Template', '{0}', '{1}',
                                                     '{2}')

    def create(self, secret_type, value=None):
        """
        Create a secret object of the specified type with the given value.

        Args:
            secret_type (ObjectType): An ObjectType enumeration specifying the
                type of secret to create.
            value (dict): A dictionary containing secret data. Optional,
                defaults to None.

        Returns:
            secret: The newly constructed secret object.

        Raises:
            TypeError: If the provided secret type is unrecognized.

        Example:
            >>> factory.create(ObjectType.SYMMETRIC_KEY)
            SymmetricKey(...)
        """
        if secret_type is ObjectType.CERTIFICATE:
            return self._create_certificate()
        elif secret_type is ObjectType.SYMMETRIC_KEY:
            return self._create_symmetric_key(value)
        elif secret_type is ObjectType.PUBLIC_KEY:
            return self._create_public_key(value)
        elif secret_type is ObjectType.PRIVATE_KEY:
            return self._create_private_key(value)
        elif secret_type is ObjectType.SPLIT_KEY:
            return self._create_split_key(value)
        elif secret_type is ObjectType.TEMPLATE:
            return self._create_template(value)
        elif secret_type is ObjectType.SECRET_DATA:
            return self._create_secret_data(value)
        elif secret_type is ObjectType.OPAQUE_DATA:
            return self._create_opaque_data(value)
        else:
            raise TypeError("Unrecognized secret type: {0}".format(
                secret_type))

    def _create_certificate(self):
        return Certificate()

    def _create_symmetric_key(self, value):
        if value is None:
            return SymmetricKey()
        else:
            key_block = self._build_key_block(value)
            return SymmetricKey(key_block)

    def _create_public_key(self, value):
        if value is None:
            return PublicKey()
        else:
            key_block = self._build_key_block(value)
            return PublicKey(key_block)

    def _create_private_key(self, value):
        if value is None:
            return PrivateKey()
        else:
            key_block = self._build_key_block(value)
            return PrivateKey(key_block)

    def _create_split_key(self, value):
        raise NotImplementedError()

    def _create_template(self, value):
        if value is None:
            return Template()
        else:
            if not isinstance(value, list):
                msg = utils.build_er_error(Template,
                                           'constructor argument type', list,
                                           type(value))
                raise TypeError(msg)
            else:
                for val in value:
                    if not isinstance(val, Attribute):
                        msg = utils.build_er_error(Template,
                                                   'constructor argument type',
                                                   Attribute, type(val))
                        raise TypeError(msg)
            return Template(value)

    def _create_secret_data(self, value):
        if value:
            kind = SecretData.SecretDataType(value.get("secret_data_type"))
            key_block = self._build_key_block(value)
            return SecretData(kind, key_block)
        return SecretData()

    def _create_opaque_data(self, value):
        if value:
            kind = OpaqueObject.OpaqueDataType(value.get("opaque_data_type"))
            data = OpaqueObject.OpaqueDataValue(value.get("opaque_data_value"))
            return OpaqueObject(kind, data)
        return OpaqueObject()

    def _build_key_block(self, value):
        key_type = value.get('key_format_type')
        key_compression_type = value.get('key_compression_type')
        key_value = value.get('key_value')
        cryptographic_algorithm = value.get('cryptographic_algorithm')
        cryptographic_length = value.get('cryptographic_length')
        key_wrapping_data = value.get('key_wrapping_data')

        key_format_type = KeyFormatType(key_type)

        key_comp_type = None
        if key_compression_type is not None:
            key_comp_type = KeyBlock.KeyCompressionType(
                key_compression_type)

        key_material = KeyMaterial(key_value)
        key_value = KeyValue(key_material)
        crypto_algorithm = CryptographicAlgorithm(cryptographic_algorithm)
        crypto_length = CryptographicLength(cryptographic_length)

        key_wrap_data = None
        if key_wrapping_data is not None:
            key_wrap_data = self._build_key_wrapping_data(key_wrapping_data)

        key_block = KeyBlock(key_format_type,
                             key_comp_type,
                             key_value,
                             crypto_algorithm,
                             crypto_length,
                             key_wrap_data)
        return key_block

    def _build_key_wrapping_data(self, wrap_data):
        wrapping_method = WrappingMethod(wrap_data.get('wrap_method'))

        enc_key_info = None
        # NOTE(2.1.5): we will use the crypto params from the identified key
        if 'encryption_key_uuid' in wrap_data:
            enc_key_info = EncryptionKeyInformation(
                unique_identifier=UniqueIdentifier(
                    wrap_data.get('encryption_key_uuid')))

        mac_key_info = None
        # NOTE(2.1.5): we will use the crypto params from the identified key
        if 'mac_key_uuid' in wrap_data:
            mac_key_info = MACSignatureKeyInformation(
                unique_identifier=UniqueIdentifier(
                    value=wrap_data.get('mac_key_uuid')))

        mac_signature = wrap_data.get('mac_signature')  # byte string
        iv_nonce = wrap_data.get('iv_counter_nonce')  # byte string

        encoding_option = None
        if 'encoding_option' in wrap_data:
            encoding_option = EncodingOption(wrap_data.get('encoding_option'))

        key_wrapping_data = KeyWrappingData(
            wrapping_method=wrapping_method,
            encryption_key_information=enc_key_info,
            mac_signature_key_information=mac_key_info,
            mac_signature=mac_signature,
            iv_counter_nonce=iv_nonce,
            encoding_option=encoding_option)

        return key_wrapping_data
