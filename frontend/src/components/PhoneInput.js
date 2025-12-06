import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const COUNTRY_CODES = [
  { code: '+91', country: 'India', flag: '🇮🇳', maxLength: 10 },
  { code: '+1', country: 'USA/Canada', flag: '🇺🇸', maxLength: 10 },
  { code: '+44', country: 'UK', flag: '🇬🇧', maxLength: 10 },
  { code: '+971', country: 'UAE', flag: '🇦🇪', maxLength: 9 },
  { code: '+965', country: 'Kuwait', flag: '🇰🇼', maxLength: 8 },
  { code: '+966', country: 'Saudi Arabia', flag: '🇸🇦', maxLength: 9 },
  { code: '+974', country: 'Qatar', flag: '🇶🇦', maxLength: 8 },
  { code: '+973', country: 'Bahrain', flag: '🇧🇭', maxLength: 8 },
  { code: '+968', country: 'Oman', flag: '🇴🇲', maxLength: 8 },
];

export default function PhoneInput({ 
  label = "Phone Number",
  countryCode = '+91',
  phoneNumber = '',
  onCountryCodeChange,
  onPhoneNumberChange,
  required = false,
  disabled = false,
  showLabel = true,
  placeholder = "Enter 10-digit number",
  error = null
}) {
  const selectedCountry = COUNTRY_CODES.find(c => c.code === countryCode) || COUNTRY_CODES[0];
  
  const handlePhoneChange = (e) => {
    const value = e.target.value.replace(/\D/g, ''); // Only digits
    if (value.length <= selectedCountry.maxLength) {
      onPhoneNumberChange(value);
    }
  };

  return (
    <div className="space-y-2">
      {showLabel && (
        <Label>
          {label} {required && <span className="text-red-500">*</span>}
        </Label>
      )}
      <div className="flex gap-2">
        {/* Country Code Dropdown */}
        <select
          value={countryCode}
          onChange={(e) => onCountryCodeChange(e.target.value)}
          disabled={disabled}
          className="flex h-10 w-32 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
        >
          {COUNTRY_CODES.map((country) => (
            <option key={country.code} value={country.code}>
              {country.flag} {country.code}
            </option>
          ))}
        </select>

        {/* Phone Number Input */}
        <Input
          type="tel"
          value={phoneNumber}
          onChange={handlePhoneChange}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          maxLength={selectedCountry.maxLength}
          className="flex-1"
        />
      </div>
      
      {/* Helper Text */}
      <p className="text-xs text-slate-500">
        Enter {selectedCountry.maxLength}-digit mobile number
      </p>
      
      {/* Error Message */}
      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}
    </div>
  );
}

// Utility function to combine country code and phone number
export const combinePhoneNumber = (countryCode, phoneNumber) => {
  return `${countryCode}${phoneNumber}`;
};

// Utility function to split full phone number into code and number
export const splitPhoneNumber = (fullNumber) => {
  if (!fullNumber) return { countryCode: '+91', phoneNumber: '' };
  
  for (const country of COUNTRY_CODES) {
    if (fullNumber.startsWith(country.code)) {
      return {
        countryCode: country.code,
        phoneNumber: fullNumber.substring(country.code.length)
      };
    }
  }
  
  // Default if no match
  return { countryCode: '+91', phoneNumber: fullNumber.replace(/^\+/, '') };
};
