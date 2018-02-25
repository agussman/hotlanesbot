import { TestBed, inject } from '@angular/core/testing';

import { TollDataService } from './toll-data.service';

describe('TollDataService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [TollDataService]
    });
  });

  it('should be created', inject([TollDataService], (service: TollDataService) => {
    expect(service).toBeTruthy();
  }));
});
