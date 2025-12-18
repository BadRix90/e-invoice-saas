import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { ApiService } from './api';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;
  const API_URL = 'http://localhost:8000/api';

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        ApiService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should fetch invoices', () => {
    const mockInvoices = [
      { id: 1, invoice_number: 'RE-2025-0001', total: '100.00' },
      { id: 2, invoice_number: 'RE-2025-0002', total: '200.00' }
    ];

    service.getInvoices().subscribe(invoices => {
      expect(invoices.length).toBe(2);
      expect(invoices[0].invoice_number).toBe('RE-2025-0001');
    });

    const req = httpMock.expectOne(`${API_URL}/invoices/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockInvoices);
  });

  it('should fetch customers', () => {
    const mockCustomers = [
      { id: 1, company_name: 'Firma A' },
      { id: 2, company_name: 'Firma B' }
    ];

    service.getCustomers().subscribe(customers => {
      expect(customers.length).toBe(2);
    });

    const req = httpMock.expectOne(`${API_URL}/customers/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockCustomers);
  });

  it('should archive invoice', () => {
    const mockResponse = { success: true, hash: 'abc123' };

    service.archiveInvoice(1).subscribe(response => {
      expect(response.success).toBe(true);
    });

    const req = httpMock.expectOne(`${API_URL}/invoices/1/archive/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);
  });
});
